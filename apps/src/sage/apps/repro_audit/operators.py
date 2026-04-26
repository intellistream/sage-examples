from __future__ import annotations

import csv
import json
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


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "present"}


class ReproManifestSource(ListBatchSource):
    def __init__(self, manifest_file: str, **kwargs):
        super().__init__(**kwargs)
        self.manifest_file = manifest_file

    def load_items(self) -> list[dict[str, Any]]:
        items = _load_records(self.manifest_file)
        for item in items:
            item.setdefault("source_path", self.manifest_file)
        return items


class ReproMetadataExtractor(MapFunction):
    REQUIRED_FIELDS = ("dataset_path", "script_path", "environment", "seed", "metric_name")

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        payload["artifact_presence"] = {
            field: bool(payload.get(field)) for field in self.REQUIRED_FIELDS
        }
        payload["run_id"] = str(payload.get("run_id") or payload.get("experiment_id") or "unknown")
        payload["result_reproduced"] = _as_bool(payload.get("result_reproduced"))
        payload["config_locked"] = _as_bool(payload.get("config_locked"))
        return payload


class ReproConsistencyChecker(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        missing = [
            field for field, present in payload.get("artifact_presence", {}).items() if not present
        ]
        issues = list(missing)
        if not payload.get("result_reproduced"):
            issues.append("result_not_reproduced")
        if not payload.get("config_locked"):
            issues.append("config_not_locked")
        payload["missing_artifacts"] = missing
        payload["consistency_issues"] = issues
        return payload


class ReproRiskScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        payload = dict(item)
        score = len(payload.get("missing_artifacts") or []) * 3 + len(
            payload.get("consistency_issues") or []
        )
        grade = "pass"
        if score >= 8:
            grade = "critical"
        elif score >= 4:
            grade = "warning"
        payload["repro_risk_score"] = score
        payload["audit_grade"] = grade
        payload["audit_summary"] = (
            f"运行 {payload.get('run_id')} 缺失 {len(payload.get('missing_artifacts') or [])} 项资产，"
            f"审计结果 {grade}。"
        )
        return payload


class ReproAuditSink(SinkFunction):
    def __init__(self, output_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.output_target = output_dir
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(dict(item))
        target = Path(self.output_target)
        if target.suffix:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        else:
            target.mkdir(parents=True, exist_ok=True)
            (target / "results.json").write_text(
                json.dumps(self.items, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
