from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


def _load_records(path_str: str) -> list[dict[str, Any]]:
    path = Path(path_str)
    if not path.exists():
        return [{"source_path": path_str, "text": path.name or path_str}]
    if path.is_dir():
        items: list[dict[str, Any]] = []
        for child in sorted(path.iterdir()):
            if child.is_file():
                items.extend(_load_records(str(child)))
        return items
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            return [item if isinstance(item, dict) else {"value": item} for item in data]
        if isinstance(data, dict):
            return [data]
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle, delimiter=delimiter))
    lines = [
        line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()
    ]
    return [
        {"text": line, "line_number": index + 1, "source_path": str(path)}
        for index, line in enumerate(lines)
    ]


def _extract_section(text: str, title: str) -> str:
    pattern = rf"{title}\s*[:：]\s*(.+?)(?:\n[A-Z][^\n]*[:：]|\Z)"
    match = re.search(pattern, text, re.I | re.S)
    return match.group(1).strip() if match else ""


class DrugLeafletSource(ListBatchSource):
    def __init__(self, input_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.input_dir = input_dir

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.input_dir)
        for item in items:
            item.setdefault("app_slug", "drug_leaflet_extractor")
            item.setdefault("source_path", self.input_dir)
        return items


class DrugLeafletTextExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        text = str(payload.get("content") or payload.get("text") or "")
        payload["leaflet_text"] = re.sub(r"\s+", " ", text).strip()
        return payload


class DrugFieldExtractor(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        text = payload.get("leaflet_text", "")
        dosage_match = re.search(r"(\d+(?:\.\d+)?)\s*(mg|g|ml)", text, re.I)
        payload["drug_name"] = str(payload.get("drug_name") or payload.get("name") or "unknown")
        payload["dosage_value"] = float(dosage_match.group(1)) if dosage_match else None
        payload["dosage_unit"] = dosage_match.group(2).lower() if dosage_match else ""
        payload["contraindications"] = _extract_section(
            text, "Contraindications"
        ) or _extract_section(text, "禁忌")
        payload["adverse_reactions"] = _extract_section(
            text, "Adverse Reactions"
        ) or _extract_section(text, "不良反应")
        payload["warnings"] = _extract_section(text, "Warnings") or _extract_section(text, "警示")
        return payload


class DrugUnitNormalizer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        unit = str(payload.get("dosage_unit") or "").lower()
        value = payload.get("dosage_value")
        normalized_dose = None
        if value is not None:
            if unit == "g":
                normalized_dose = f"{value * 1000:.0f} mg"
            elif unit == "ml":
                normalized_dose = f"{value:.0f} ml"
            else:
                normalized_dose = f"{value:.0f} mg"
        payload["normalized_dose"] = normalized_dose or "unknown"
        payload["risk_flags"] = [
            flag
            for flag, section in (
                ("contraindication_present", payload.get("contraindications")),
                ("adverse_reaction_present", payload.get("adverse_reactions")),
                ("warning_present", payload.get("warnings")),
            )
            if section
        ]
        return payload


class DrugLeafletSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8")
