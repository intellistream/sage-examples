"""
Resume Parser Operators

Custom operators for resume parsing and standardization.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import CustomLogger, MapFunction, SinkFunction


class ResumeSource(ListBatchSource):
    """Read resume text files and return them as batch."""

    def __init__(
        self, resume_dir: str | None = None, resume_files: list[str] | None = None, **kwargs
    ):
        """Initialize resume source.

        Args:
            resume_dir: Directory containing resume files
            resume_files: List of resume file paths
        """
        super().__init__(**kwargs)
        self.resume_dir = resume_dir
        self.resume_files = resume_files or []
        self._logger = CustomLogger("ResumeSource")

    def load_items(self) -> list[dict[str, str]]:
        """Read and return all resume files."""
        import os

        resumes = []
        files_to_process = []

        if self.resume_dir and os.path.isdir(self.resume_dir):
            files_to_process = [
                os.path.join(self.resume_dir, f)
                for f in os.listdir(self.resume_dir)
                if f.endswith((".txt", ".md"))
            ]

        files_to_process.extend(self.resume_files)

        for file_path in files_to_process:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                    resumes.append(
                        {
                            "filename": file_path,
                            "content": content,
                        }
                    )
            except Exception as e:
                self.logger.error(f"Error reading {file_path}: {e}")

        self.logger.info(f"Read {len(resumes)} resume files")
        return resumes


class TextExtractor(MapFunction):
    def execute(self, resume: dict[str, str]) -> dict[str, Any]:
        enriched = dict(resume)
        enriched["text"] = resume.get("content", "")
        return enriched


class ResumeInfoExtractor(MapFunction):
    """Extract structured information from resume text."""

    def __init__(self, **kwargs):
        """Initialize resume info extractor."""
        super().__init__(**kwargs)
        self._logger = CustomLogger("ResumeInfoExtractor")

    def execute(self, resume: dict[str, str]) -> dict[str, Any]:
        """Extract information from resume.

        Args:
            resume: Resume dict with 'content' key

        Returns:
            Dict with extracted fields
        """
        if not resume or "content" not in resume:
            return resume

        content = resume["content"]
        result = {"filename": resume.get("filename", "")}

        # Extract name (usually at the beginning)
        lines = content.split("\n")
        name_candidates = [line.strip() for line in lines[:5] if line.strip()]
        result["name"] = name_candidates[0] if name_candidates else "Unknown"

        # Extract email
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, content)
        result["email"] = emails[0] if emails else ""

        # Extract phone (Chinese phone: 11 digits or +86)
        phone_pattern = r"(\+?86)?1[3-9]\d{9}"
        phones = re.findall(phone_pattern, content)
        result["phone"] = phones[0] if phones else ""

        # Extract education
        edu_pattern = r"(瀛﹀＋|纭曞＋|鍗氬＋|Bachelor|Master|PhD|鏈|涓撶)"
        educations = re.findall(edu_pattern, content)
        result["education_level"] = educations[0] if educations else ""

        # Extract years of experience (look for patterns like "N骞村伐浣滅粡楠?)
        exp_pattern = r"(\d+)\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|work)"
        exp_matches = re.findall(exp_pattern, content)
        if exp_matches:
            result["years_experience"] = int(exp_matches[0][0])
        else:
            result["years_experience"] = 0

        # Extract skills
        skills = []
        for line in lines:
            if any(keyword in line for keyword in ["Skills", "Competencies", "Skill"]):
                # Extract subsequent lines as skills
                idx = lines.index(line)
                for skill_line in lines[idx + 1 : idx + 5]:
                    if skill_line.strip():
                        skills.extend([s.strip() for s in skill_line.split(",") if s.strip()])
        result["skills"] = skills[:10]  # Top 10 skills

        # Extract companies/positions
        positions = []
        company_pattern = r"(鍏徃|Company|Inc\.|Corp\.)"
        for i, line in enumerate(lines):
            if re.search(company_pattern, line) and i + 1 < len(lines):
                positions.append(
                    {
                        "company": line.strip(),
                        "title": lines[i + 1].strip() if i + 1 < len(lines) else "",
                    }
                )
        result["positions"] = positions[:5]  # Top 5 positions

        return result


class InfoExtractor(ResumeInfoExtractor):
    pass


class ResumeNormalizer(MapFunction):
    """Normalize resume information."""

    def __init__(self, **kwargs):
        """Initialize resume normalizer."""
        super().__init__(**kwargs)

    def execute(self, resume: dict[str, Any]) -> dict[str, Any]:
        """Normalize resume data.

        Args:
            resume: Extracted resume data

        Returns:
            Normalized resume data
        """
        if not resume:
            return resume

        # Normalize name (title case)
        if "name" in resume:
            resume["name"] = resume["name"].title()

        # Normalize email (lowercase)
        if "email" in resume:
            resume["email"] = resume["email"].lower()

        # Normalize education level
        education_mapping = {
            "瀛﹀＋": "Bachelor",
            "纭曞＋": "Master",
            "鍗氬＋": "PhD",
            "鏈": "Bachelor",
            "涓撶": "Associate",
            "楂樹腑": "High School",
        }
        edu = resume.get("education_level", "")
        resume["education_level"] = education_mapping.get(edu, edu)

        # Ensure years_experience is int
        if "years_experience" in resume:
            resume["years_experience"] = int(resume["years_experience"])

        # Normalize skills (lowercase, deduplicate)
        if "skills" in resume:
            resume["skills"] = list({skill.lower() for skill in resume["skills"]})

        # Add processing timestamp
        resume["processed_at"] = datetime.now().isoformat()

        return resume


class DateNormalizer(ResumeNormalizer):
    def execute(self, resume: dict[str, Any]) -> dict[str, Any]:
        normalized = super().execute(resume)
        for position in normalized.get("positions", []):
            if "date" in position and isinstance(position["date"], str):
                position["date"] = position["date"].replace("/", "-")
        return normalized


class ResumeValidator(MapFunction):
    """Validate resume completeness."""

    def __init__(self, required_fields: list[str] | None = None, **kwargs):
        """Initialize resume validator.

        Args:
            required_fields: List of required fields
        """
        super().__init__(**kwargs)
        self.required_fields = required_fields or ["name", "email", "phone"]
        self._logger = CustomLogger("ResumeValidator")

    def execute(self, resume: dict[str, Any]) -> dict[str, Any]:
        """Validate resume.

        Args:
            resume: Resume data

        Returns:
            Resume with validation markers
        """
        if not resume:
            return resume

        # Check required fields
        missing_fields = [f for f in self.required_fields if not resume.get(f)]
        resume["is_complete"] = len(missing_fields) == 0
        resume["missing_fields"] = missing_fields
        resume["completeness_score"] = (
            (len(self.required_fields) - len(missing_fields)) / len(self.required_fields) * 100
        )

        return resume


class ResumeSink(SinkFunction):
    """Output parsed resumes to JSON file."""

    def __init__(self, output_file: str, **kwargs):
        """Initialize resume sink.

        Args:
            output_file: Path to output JSON file
        """
        super().__init__(**kwargs)
        self.output_file = output_file
        self._logger = CustomLogger("ResumeSink")
        self.count = 0

    def setup(self, context: Any) -> None:
        """Setup - prepare output file."""
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("[\n")

    def execute(self, resume: dict[str, Any]) -> None:
        """Append resume to JSON file.

        Args:
            resume: Parsed resume
        """
        if not resume:
            return

        with open(self.output_file, "a", encoding="utf-8") as f:
            if self.count > 0:
                f.write(",\n")
            json.dump(resume, f, ensure_ascii=False, default=str, indent=2)
            self.count += 1

    def teardown(self, context: Any) -> None:
        """Cleanup - close JSON array."""
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write("\n]")
        self.logger.info(f"Written {self.count} parsed resumes to {self.output_file}")
