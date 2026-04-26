"""
Data Cleaner Operators

Custom operators for CSV/Excel data cleaning and standardization.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import CustomLogger, MapFunction, SinkFunction


class CsvSource(ListBatchSource):
    """Read CSV/Excel file and return rows as batch."""

    def __init__(self, input_file: str, delimiter: str = ",", **kwargs):
        """Initialize CSV source.

        Args:
            input_file: Path to CSV file
            delimiter: CSV delimiter (default: ",")
        """
        super().__init__(**kwargs)
        self.input_file = input_file
        self.delimiter = delimiter
        self._logger = CustomLogger("CsvSource")

    def load_items(self) -> list[dict[str, str]]:
        """Read and return all CSV rows as dictionaries."""
        try:
            rows = []
            with open(self.input_file, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                if reader.fieldnames is None:
                    self.logger.error(f"Empty CSV file: {self.input_file}")
                    return []

                for row in reader:
                    rows.append(row)

            self.logger.info(f"Read {len(rows)} rows from {self.input_file}")
            return rows
        except FileNotFoundError:
            self.logger.error(f"CSV file not found: {self.input_file}")
            return []
        except Exception as e:
            self.logger.error(f"Error reading CSV: {e}")
            return []


class TypeConverter(MapFunction):
    """Convert field types according to rules."""

    def __init__(self, type_rules: dict[str, str] | None = None, **kwargs):
        """Initialize type converter.

        Args:
            type_rules: Dict mapping field names to types (int, float, bool, date)
                Example: {"age": "int", "salary": "float", "active": "bool"}
        """
        super().__init__(**kwargs)
        self.type_rules = type_rules or {}
        self._logger = CustomLogger("TypeConverter")

    def _convert_value(self, value: str, target_type: str) -> Any:
        """Convert a value to target type.

        Args:
            value: Value string to convert
            target_type: Target type (int, float, bool, date)

        Returns:
            Converted value or original if conversion fails
        """
        if not value or value.strip() == "":
            return None

        value = value.strip()

        try:
            if target_type.lower() == "int":
                return int(float(value))  # Handle decimal strings like "5.0"
            elif target_type.lower() == "float":
                return float(value)
            elif target_type.lower() == "bool":
                return value.lower() in ["true", "yes", "1", "on"]
            elif target_type.lower() == "date":
                # Try common date formats
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m-%d-%Y"]:
                    try:
                        return datetime.strptime(value, fmt).isoformat()
                    except ValueError:
                        continue
                return value  # Return as-is if no format matches
            else:
                return value
        except (ValueError, TypeError):
            return value  # Return original value if conversion fails

    def execute(self, row: dict[str, str]) -> dict[str, Any]:
        """Convert field types in a row.

        Args:
            row: Data row

        Returns:
            Row with converted types
        """
        if not row:
            return row

        result = dict(row)  # Copy original

        for field, target_type in self.type_rules.items():
            if field in result:
                result[field] = self._convert_value(result[field], target_type)

        return result


class MissingValueFiller(MapFunction):
    """Fill missing values according to strategy."""

    def __init__(self, fill_strategy: dict[str, str] | str | None = None, **kwargs):
        """Initialize missing value filler.

        Args:
            fill_strategy: Strategy per field or global strategy
                Field-level: {"age": "0", "name": "Unknown"}
                Global: "drop" (drop rows), "mean" (use mean), "forward" (forward fill)
        """
        super().__init__(**kwargs)
        self.fill_strategy = fill_strategy or "drop"
        self._logger = CustomLogger("MissingValueFiller")
        self.row_count = 0
        self.dropped_count = 0

    def execute(self, row: dict[str, Any]) -> dict[str, Any] | None:
        """Fill missing values in a row.

        Args:
            row: Data row

        Returns:
            Row with filled values or None if dropped
        """
        if not row:
            return None

        self.row_count += 1

        # Check for missing values
        missing_fields = [k for k, v in row.items() if v is None or v == ""]

        if not missing_fields:
            return row

        # Apply fill strategy
        if isinstance(self.fill_strategy, dict):
            # Field-specific strategies
            for field in missing_fields:
                if field in self.fill_strategy:
                    row[field] = self.fill_strategy[field]
                else:
                    row[field] = None
            return row

        elif self.fill_strategy == "drop":
            # Drop rows with missing values
            self.dropped_count += 1
            return None

        elif self.fill_strategy == "forward":
            # Fill with empty string (forward fill would require state)
            for field in missing_fields:
                row[field] = ""
            return row

        else:
            # Default: return as-is
            return row

    def teardown(self, context: Any) -> None:
        """Log statistics."""
        if self.dropped_count > 0:
            self.logger.info(
                f"Dropped {self.dropped_count}/{self.row_count} rows with missing values"
            )


class AnomalyDetector(MapFunction):
    """Detect anomalies in numeric fields."""

    def __init__(self, numeric_fields: list[str] | None = None, **kwargs):
        """Initialize anomaly detector.

        Args:
            numeric_fields: List of numeric field names to check
        """
        super().__init__(**kwargs)
        self.numeric_fields = numeric_fields or []
        self._logger = CustomLogger("AnomalyDetector")

    def execute(self, row: dict[str, Any]) -> dict[str, Any]:
        """Detect anomalies in a row.

        Adds:
        - has_anomaly: boolean flag
        - anomaly_fields: list of fields with anomalies
        - anomalies: dict of detected anomalies

        Args:
            row: Data row

        Returns:
            Row with anomaly markers
        """
        if not row:
            return row

        row["has_anomaly"] = False
        row["anomaly_fields"] = []
        row["anomalies"] = {}

        for field in self.numeric_fields:
            if field not in row:
                continue

            value = row[field]

            # Skip non-numeric values
            if not isinstance(value, (int, float)):
                continue

            # Check for negative values where not expected
            if value < 0 and field.lower() not in ["change", "delta", "difference"]:
                row["has_anomaly"] = True
                row["anomaly_fields"].append(field)
                row["anomalies"][field] = f"negative_value: {value}"

            # Check for extremely large values
            if value > 1e9:
                row["has_anomaly"] = True
                row["anomaly_fields"].append(field)
                row["anomalies"][field] = f"extremely_large: {value}"

        return row


class DuplicateMarker(MapFunction):
    """Mark potential duplicate rows based on key fields."""

    def __init__(self, key_fields: list[str] | None = None, **kwargs):
        """Initialize duplicate marker.

        Args:
            key_fields: Fields to use for duplicate detection
        """
        super().__init__(**kwargs)
        self.key_fields = key_fields or []
        self.seen_keys = {}
        self._logger = CustomLogger("DuplicateMarker")

    def execute(self, row: dict[str, Any]) -> dict[str, Any]:
        """Mark duplicates based on key fields.

        Args:
            row: Data row

        Returns:
            Row with duplicate markers
        """
        if not row:
            return row

        # Build key from key fields
        if self.key_fields:
            key_values = tuple(row.get(f, "") for f in self.key_fields)
            is_duplicate = key_values in self.seen_keys
            row["is_duplicate"] = is_duplicate
            row["duplicate_index"] = self.seen_keys.get(key_values, 0)

            if not is_duplicate:
                self.seen_keys[key_values] = 1
            else:
                self.seen_keys[key_values] += 1
        else:
            row["is_duplicate"] = False
            row["duplicate_index"] = 0

        return row


class CleanedDataSink(SinkFunction):
    """Output cleaned data to CSV file."""

    def __init__(self, output_file: str, **kwargs):
        """Initialize cleaned data sink.

        Args:
            output_file: Path to output CSV file
        """
        super().__init__(**kwargs)
        self.output_file = output_file
        self._logger = CustomLogger("CleanedDataSink")
        self.count = 0
        self.fieldnames = None
        self.writer = None
        self.file = None

    def setup(self, context: Any) -> None:
        """Setup - open output file."""
        self.file = open(self.output_file, "w", newline="", encoding="utf-8")

    def execute(self, row: dict[str, Any]) -> None:
        """Write cleaned row to CSV.

        Args:
            row: Cleaned data row
        """
        if not row:
            return

        if self.file is None:
            self.file = open(self.output_file, "w", newline="", encoding="utf-8")

        # Initialize writer on first row
        if self.writer is None:
            self.fieldnames = list(row.keys())
            self.writer = csv.DictWriter(self.file, fieldnames=self.fieldnames)
            self.writer.writeheader()

        self.writer.writerow({k: row.get(k, "") for k in self.fieldnames})
        self.file.flush()
        self.count += 1

    def teardown(self, context: Any) -> None:
        """Cleanup - close output file."""
        if self.file:
            self.file.close()
        self.logger.info(f"Written {self.count} cleaned rows to {self.output_file}")


class JsonSink(SinkFunction):
    """Output cleaned data to JSON file."""

    def __init__(self, output_file: str, **kwargs):
        """Initialize JSON sink.

        Args:
            output_file: Path to output JSON file
        """
        super().__init__(**kwargs)
        self.output_file = output_file
        self._logger = CustomLogger("JsonSink")
        self.count = 0
        self.items: list[dict[str, Any]] = []

    def setup(self, context: Any) -> None:
        """Setup - prepare output file."""
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("[\n")

    def execute(self, row: dict[str, Any]) -> None:
        """Append row to JSON file.

        Args:
            row: Data row
        """
        if not row:
            return

        self.items.append(row)
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False, default=str, indent=2)
        self.count += 1

    def teardown(self, context: Any) -> None:
        """Cleanup - close JSON array."""
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write("\n]")
        self.logger.info(f"Written {self.count} rows to {self.output_file}")
