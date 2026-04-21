"""
Log Parser Operators

Custom operators for log parsing and structuring.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


class LogSource(ListBatchSource):
    """Read log file line by line as a batch."""

    def __init__(self, log_file: str, **kwargs):
        """Initialize log source.

        Args:
            log_file: Path to the log file to read
        """
        super().__init__(**kwargs)
        self.log_file = log_file
        self._logger = CustomLogger("LogSource")

    def load_items(self) -> list[str]:
        """Read and return all log lines."""
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = [line.rstrip("\n") for line in f if line.strip()]
            self.logger.info(f"Read {len(lines)} log lines from {self.log_file}")
            return lines
        except FileNotFoundError:
            self.logger.error(f"Log file not found: {self.log_file}")
            return []


class LogParser(MapFunction):
    """Parse log lines and extract structured fields.

    Supports multiple log formats:
    - Apache/Nginx: [timestamp] level message
    - Standard: timestamp level [component] message
    - JSON: JSON-formatted log lines
    """

    def __init__(self, **kwargs):
        """Initialize log parser."""
        super().__init__(**kwargs)
        self._logger = CustomLogger("LogParser")

        # Common log patterns
        self.patterns = {
            "apache": re.compile(r"\[(?P<timestamp>[^\]]+)\]\s+(?P<level>\w+)\s+(?P<message>.+)"),
            "standard": re.compile(
                r"(?P<timestamp>\S+)\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<message>.+)"
            ),
            "json": re.compile(r"^\{.*\}$"),
        }

    def execute(self, line: str) -> dict[str, Any] | None:
        """Parse a single log line.

        Args:
            line: A log line to parse

        Returns:
            Parsed log dict or None if unparseable
        """
        if not line:
            return None

        # Try JSON format first
        if self.patterns["json"].match(line):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                pass

        # Try standard format
        match = self.patterns["standard"].match(line)
        if match:
            return match.groupdict()

        # Try Apache format
        match = self.patterns["apache"].match(line)
        if match:
            return match.groupdict()

        # Fallback: return raw line with default structure
        return {
            "timestamp": datetime.now().isoformat(),
            "level": "UNKNOWN",
            "message": line,
        }


class ErrorFilter(MapFunction):
    """Filter logs by error level.

    Keeps only ERROR, CRITICAL, and WARN logs by default.
    """

    def __init__(self, error_levels: list[str] | None = None, **kwargs):
        """Initialize error filter.

        Args:
            error_levels: List of log levels to keep (e.g., ['ERROR', 'CRITICAL'])
        """
        super().__init__(**kwargs)
        self.error_levels = error_levels or ["ERROR", "CRITICAL", "WARN"]
        self._logger = CustomLogger("ErrorFilter")

    def execute(self, log_entry: dict[str, Any]) -> dict[str, Any] | None:
        """Filter log by error level.

        Args:
            log_entry: Parsed log entry

        Returns:
            Log entry if matches error level, None otherwise
        """
        if not log_entry:
            return None

        level = log_entry.get("level", "").upper()
        if level in self.error_levels:
            return log_entry

        return None


class LogEnricher(MapFunction):
    """Enrich log entries with additional computed fields."""

    def __init__(self, **kwargs):
        """Initialize log enricher."""
        super().__init__(**kwargs)

    def execute(self, log_entry: dict[str, Any]) -> dict[str, Any]:
        """Enrich a log entry.

        Adds:
        - is_critical: boolean flag for critical logs
        - message_length: length of message
        - has_error_code: whether message contains error codes
        - error_code: extracted error code if present

        Args:
            log_entry: Parsed log entry

        Returns:
            Enriched log entry
        """
        if not log_entry:
            return log_entry

        # Mark critical logs
        level = log_entry.get("level", "").upper()
        log_entry["is_critical"] = level in ["ERROR", "CRITICAL"]

        # Message length
        message = log_entry.get("message", "")
        log_entry["message_length"] = len(message)

        # Extract error codes (e.g., ERR001, ERROR_CODE_500)
        error_code_match = re.search(r"(ERR\d+|ERROR_\w+|ERROR\s*#\d+|\b[45]\d{2}\b)", message)
        if error_code_match:
            log_entry["error_code"] = error_code_match.group(1)
            log_entry["has_error_code"] = True
        else:
            log_entry["has_error_code"] = False
            log_entry["error_code"] = None

        return log_entry


class JsonSink(SinkFunction):
    """Output structured logs to JSON file."""

    def __init__(self, output_file: str, **kwargs):
        """Initialize JSON sink.

        Args:
            output_file: Path to output JSON file
        """
        super().__init__(**kwargs)
        self.output_file = output_file
        self._logger = CustomLogger("JsonSink")
        self.count = 0

    def setup(self, context: Any) -> None:
        """Setup - prepare output file."""
        # Clear existing file
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("[\n")

    def execute(self, log_entry: dict[str, Any]) -> None:
        """Append log entry to JSON file.

        Args:
            log_entry: Parsed and enriched log entry
        """
        if not log_entry:
            return

        with open(self.output_file, "a", encoding="utf-8") as f:
            if self.count > 0:
                f.write(",\n")
            json.dump(log_entry, f, ensure_ascii=False, indent=2)
            self.count += 1

    def teardown(self, context: Any) -> None:
        """Cleanup - close JSON array."""
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write("\n]")
        self.logger.info(f"Written {self.count} log entries to {self.output_file}")


class ConsoleSink(SinkFunction):
    """Output logs to console with formatting."""

    def __init__(self, **kwargs):
        """Initialize console sink."""
        super().__init__(**kwargs)
        self._logger = CustomLogger("ConsoleSink")
        self.count = 0

    def execute(self, log_entry: dict[str, Any]) -> None:
        """Print formatted log entry to console.

        Args:
            log_entry: Log entry to print
        """
        if not log_entry:
            return

        timestamp = log_entry.get("timestamp", "N/A")
        level = log_entry.get("level", "UNKNOWN")
        message = log_entry.get("message", "")
        error_code = log_entry.get("error_code", "")

        error_code_str = f" [{error_code}]" if error_code else ""
        print(f"{timestamp} {level}{error_code_str}: {message}")
        self.count += 1

    def teardown(self, context: Any) -> None:
        """Cleanup."""
        self.logger.info(f"Displayed {self.count} log entries")
