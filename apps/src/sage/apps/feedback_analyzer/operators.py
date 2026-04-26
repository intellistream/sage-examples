"""
Feedback Analyzer Operators

Custom operators for customer feedback analysis and keyword extraction.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import CustomLogger, FlatMapFunction, MapFunction, SinkFunction


class FeedbackSource(ListBatchSource):
    """Read feedback data from text file or CSV."""

    def __init__(self, feedback_file: str, delimiter: str = "\t", **kwargs):
        """Initialize feedback source.

        Args:
            feedback_file: Path to feedback file
            delimiter: Delimiter for CSV format (default: tab)
        """
        super().__init__(**kwargs)
        self.feedback_file = feedback_file
        self.delimiter = delimiter
        self._logger = CustomLogger("FeedbackSource")

    def load_items(self) -> list[dict[str, str]]:
        """Read and return all feedback entries."""
        import csv

        feedbacks = []
        try:
            with open(self.feedback_file, encoding="utf-8") as f:
                # Try CSV format first
                reader = csv.DictReader(f, delimiter=self.delimiter)
                if reader.fieldnames and len(reader.fieldnames) > 1:
                    for row in reader:
                        feedbacks.append(row)
                else:
                    # Fall back to line-by-line
                    f.seek(0)
                    for i, line in enumerate(f):
                        feedbacks.append(
                            {
                                "id": str(i),
                                "text": line.strip(),
                            }
                        )

            self.logger.info(f"Read {len(feedbacks)} feedback entries")
            return feedbacks
        except Exception as e:
            self.logger.error(f"Error reading feedback file: {e}")
            return []


class TextCleaner(MapFunction):
    """Clean and preprocess feedback text."""

    def __init__(self, **kwargs):
        """Initialize text cleaner."""
        super().__init__(**kwargs)

    def execute(self, feedback: dict[str, str]) -> dict[str, str]:
        """Clean feedback text.

        Args:
            feedback: Feedback entry

        Returns:
            Feedback with cleaned text
        """
        if not feedback or "text" not in feedback:
            return feedback

        text = feedback.get("text", "")

        # Remove URLs
        text = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "",
            text,
        )

        # Remove email addresses
        text = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "", text)

        # Remove special characters but keep spaces
        text = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)

        # Remove extra whitespace
        text = " ".join(text.split())

        feedback["cleaned_text"] = text
        return feedback


class SimpleTokenizer(FlatMapFunction):
    """Tokenize text into words (simplified tokenizer)."""

    def __init__(self, min_length: int = 2, **kwargs):
        """Initialize tokenizer.

        Args:
            min_length: Minimum token length
        """
        super().__init__(**kwargs)
        self.min_length = min_length

    def execute(self, feedback: dict[str, str]) -> list[dict[str, Any]]:
        """Tokenize feedback text.

        Args:
            feedback: Feedback entry

        Returns:
            List of token entries
        """
        if not feedback or "cleaned_text" not in feedback:
            return []

        text = feedback.get("cleaned_text", "").lower()
        feedback_id = feedback.get("id", "")

        # Simple space-based tokenization
        # For Chinese, this is a simplification; production would use jieba or similar
        tokens = [t for t in text.split() if len(t) >= self.min_length]

        # Also extract common Chinese bigrams if present
        if any("\u4e00" <= c <= "\u9fff" for c in text):
            # Simple 2-character extraction
            for i in range(len(text) - 1):
                if all("\u4e00" <= c <= "\u9fff" for c in text[i : i + 2]):
                    tokens.append(text[i : i + 2])

        return [
            {
                "feedback_id": feedback_id,
                "token": token,
                "length": len(token),
            }
            for token in tokens
        ]


class KeywordScorer(MapFunction):
    """Score keywords based on frequency and relevance."""

    def __init__(self, common_words: list[str] | None = None, **kwargs):
        """Initialize keyword scorer.

        Args:
            common_words: List of common words to exclude
        """
        super().__init__(**kwargs)
        self.common_words = set(
            common_words
            or [
                "the",
                "a",
                "an",
                "is",
                "are",
                "was",
                "were",
                "be",
                "have",
                "has",
                "this",
                "that",
                "with",
                "from",
                "your",
                "their",
                "our",
                "for",
                "and",
                "but",
            ]
        )
        self.token_count = {}
        self.feedback_count = {}

    def execute(self, token_entry: dict[str, Any]) -> dict[str, Any]:
        """Score a token entry.

        Args:
            token_entry: Token information

        Returns:
            Token with score markers
        """
        if not token_entry:
            return token_entry

        token = token_entry.get("token", "").lower()

        # Skip common words
        if token in self.common_words:
            token_entry["is_stopword"] = True
            return token_entry

        # Count frequency
        self.token_count[token] = self.token_count.get(token, 0) + 1

        # Mark non-stopword
        token_entry["is_stopword"] = False

        return token_entry


class KeywordExtractor(MapFunction):
    """Extract top keywords from aggregated data."""

    def __init__(self, top_n: int = 20, **kwargs):
        """Initialize keyword extractor.

        Args:
            top_n: Number of top keywords to extract
        """
        super().__init__(**kwargs)
        self.top_n = top_n
        self._logger = CustomLogger("KeywordExtractor")
        self.keyword_stats = {}

    def execute(self, token_entry: dict[str, Any]) -> dict[str, Any] | None:
        """Extract keyword information.

        Args:
            token_entry: Token entry

        Returns:
            Enhanced token or None
        """
        if not token_entry or token_entry.get("is_stopword"):
            return None

        token = token_entry.get("token", "")
        if token not in self.keyword_stats:
            self.keyword_stats[token] = {
                "count": 0,
                "feedback_count": 1,
                "first_seen": datetime.now().isoformat(),
            }

        self.keyword_stats[token]["count"] += 1

        token_entry["keyword_score"] = self.keyword_stats[token]["count"]

        return token_entry

    def teardown(self, context: Any) -> None:
        """Log top keywords."""
        if self.keyword_stats:
            top_keywords = sorted(
                self.keyword_stats.items(), key=lambda x: x[1]["count"], reverse=True
            )[: self.top_n]

            self.logger.info(f"Top {len(top_keywords)} keywords extracted:")
            for keyword, stats in top_keywords:
                self.logger.info(f"  {keyword}: {stats['count']} occurrences")


class StatisticsSink(SinkFunction):
    """Output keyword statistics to JSON file."""

    def __init__(self, output_file: str, **kwargs):
        """Initialize statistics sink.

        Args:
            output_file: Path to output JSON file
        """
        super().__init__(**kwargs)
        self.output_file = output_file
        self._logger = CustomLogger("StatisticsSink")
        self.keywords = Counter()
        self.total_tokens = 0

    def execute(self, token_entry: dict[str, Any]) -> None:
        """Process token entry.

        Args:
            token_entry: Token with score
        """
        if not token_entry:
            return

        token = token_entry.get("token", "")
        score = token_entry.get("keyword_score", 1)

        self.keywords[token] += score
        self.total_tokens += 1

    def teardown(self, context: Any) -> None:
        """Write statistics to file."""
        stats = {
            "total_tokens": self.total_tokens,
            "unique_keywords": len(self.keywords),
            "generated_at": datetime.now().isoformat(),
            "top_keywords": [
                {
                    "keyword": keyword,
                    "count": count,
                    "percentage": round(count / self.total_tokens * 100, 2),
                }
                for keyword, count in self.keywords.most_common(50)
            ],
        }

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Statistics written to {self.output_file}")
        self.logger.info(
            f"Processed {self.total_tokens} tokens, {len(self.keywords)} unique keywords"
        )
