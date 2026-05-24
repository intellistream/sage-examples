"""Build reproducible public vulnerability datasets for the ICPP demo."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.request
from pathlib import Path
from typing import Any, Iterable

CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def build_cisa_kev_dataset(*, limit: int | None = None) -> list[dict[str, Any]]:
    payload = _download_json(CISA_KEV_URL)
    rows = payload.get("vulnerabilities", []) if isinstance(payload, dict) else []
    events = [_normalize_cisa_kev(item) for item in rows if isinstance(item, dict)]
    events.sort(key=lambda item: (item["timestamp"], item["event_id"]))
    if limit is not None:
        return events[:limit]
    return events


def write_dataset(events: Iterable[dict[str, Any]], output_dir: Path, *, dataset_id: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    event_list = list(events)
    events_path = output_dir / "events.jsonl"
    with events_path.open("w", encoding="utf-8") as handle:
        for item in event_list:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")

    manifest = {
        "dataset_id": dataset_id,
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_urls": [CISA_KEV_URL],
        "record_count": len(event_list),
        "events_path": str(events_path),
        "schema": "sageflow_service_demo.raw_events.v1",
    }
    manifest_path = output_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2, sort_keys=True)
    return manifest


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                events.append(json.loads(line))
    return events


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["cisa-kev"], default="cisa-kev")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dataset-id", default="cisa-kev")
    args = parser.parse_args(argv)

    if args.source != "cisa-kev":
        raise ValueError(f"unsupported source: {args.source}")
    events = build_cisa_kev_dataset(limit=args.limit)
    manifest = write_dataset(events, args.out, dataset_id=args.dataset_id)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _normalize_cisa_kev(item: dict[str, Any]) -> dict[str, Any]:
    cve_id = str(item.get("cveID", "")).strip()
    vendor = str(item.get("vendorProject", "")).strip()
    product = str(item.get("product", "")).strip()
    title = str(item.get("vulnerabilityName", "")).strip()
    summary = str(item.get("shortDescription", "")).strip()
    date_added = str(item.get("dateAdded", "")).strip() or "1970-01-01"
    due_date = str(item.get("dueDate", "")).strip()
    ransomware = str(item.get("knownRansomwareCampaignUse", "")).strip()
    tags = ["cisa-kev", "known-exploited"]
    if vendor:
        tags.append(_tag(vendor))
    if product:
        tags.append(_tag(product))
    if ransomware.lower() == "known":
        tags.append("ransomware")

    return {
        "event_id": cve_id.lower(),
        "source": "cisa_kev",
        "timestamp": f"{date_added}T00:00:00Z",
        "summary": " ".join(part for part in [title, summary] if part),
        "severity": 0.95,
        "tags": tags,
        "metadata": {
            "title": title,
            "vendor": vendor,
            "product": product,
            "due_date": due_date,
            "required_action": item.get("requiredAction", ""),
            "known_ransomware_campaign_use": ransomware,
            "source_url": CISA_KEV_URL,
        },
    }


def _download_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _tag(value: str) -> str:
    return "-".join(value.lower().replace("/", " ").replace("_", " ").split())


if __name__ == "__main__":
    raise SystemExit(main())
