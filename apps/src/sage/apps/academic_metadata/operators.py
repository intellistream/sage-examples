"""Operators for academic metadata extraction."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import CustomLogger, MapFunction, SinkFunction


class PdfSource(ListBatchSource):
    def __init__(self, input_path: str, **kwargs):
        super().__init__(**kwargs)
        self.input_path = Path(input_path)
        self._logger = CustomLogger("PdfSource")

    def load_items(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        if self.input_path.is_dir():
            for file_path in sorted(self.input_path.iterdir()):
                if file_path.is_file() and file_path.suffix.lower() in {".txt", ".md"}:
                    items.append(
                        {
                            "source_file": str(file_path),
                            "text": file_path.read_text(encoding="utf-8"),
                        }
                    )
        elif self.input_path.suffix.lower() == ".csv":
            with self.input_path.open("r", encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    items.append(
                        {"source_file": row.get("source_file", ""), "text": row.get("text", "")}
                    )
        else:
            items.append(
                {
                    "source_file": str(self.input_path),
                    "text": self.input_path.read_text(encoding="utf-8"),
                }
            )
        self.logger.info(f"Loaded {len(items)} academic documents")
        return items


class TextExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        result = dict(item)
        result["text"] = str(item.get("text", ""))
        return result


class MetadataExtractor(MapFunction):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._logger = CustomLogger("MetadataExtractor")

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = item.get("text", "")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        title = lines[0] if lines else ""
        doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", text, flags=re.IGNORECASE)
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        email_matches = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        author_line = ""
        for line in lines[1:6]:
            if "," in line or " and " in line.lower() or len(line.split()) <= 12:
                author_line = line
                break
        authors = [part.strip() for part in re.split(r",| and |;", author_line) if part.strip()]
        result = dict(item)
        result.update(
            {
                "title": title,
                "authors": authors,
                "year": year_match.group(0) if year_match else "",
                "doi": doi_match.group(0) if doi_match else "",
                "emails": email_matches,
                "abstract": self._extract_abstract(text),
            }
        )
        return result

    def _extract_abstract(self, text: str) -> str:
        lowered = text.lower()
        marker = lowered.find("abstract")
        if marker == -1:
            return ""

        snippet = text[marker:]
        lines = [line.strip() for line in snippet.splitlines()]
        abstract_lines: list[str] = []
        started = False
        for line in lines:
            if not started:
                if line.lower().startswith("abstract"):
                    remainder = line.split(":", 1)[1].strip() if ":" in line else ""
                    if remainder:
                        abstract_lines.append(remainder)
                    started = True
                continue

            lowered_line = line.lower()
            if not line or lowered_line.startswith("keywords"):
                break
            abstract_lines.append(line)

        return " ".join(abstract_lines).strip()[:1200]


class AuthorNormalizer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        normalized = []
        for author in item.get("authors", []):
            cleaned = " ".join(author.replace("*", " ").split())
            if cleaned:
                normalized.append(cleaned.title())
        item["authors"] = normalized
        item["has_complete_metadata"] = bool(item.get("title") and item.get("authors"))
        return item


class MetadataSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(item)

    def teardown(self, context: Any) -> None:
        with open(self.output_file, "w", encoding="utf-8") as handle:
            json.dump(self.items, handle, ensure_ascii=False, indent=2)
