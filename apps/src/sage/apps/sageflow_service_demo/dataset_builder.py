"""Build reproducible public vulnerability datasets for the ICPP demo."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def build_cisa_kev_dataset(*, limit: int | None = None) -> list[dict[str, Any]]:
    payload = _download_json(CISA_KEV_URL)
    rows = payload.get("vulnerabilities", []) if isinstance(payload, dict) else []
    events = [_normalize_cisa_kev(item) for item in rows if isinstance(item, dict)]
    events.sort(key=lambda item: (item["timestamp"], item["event_id"]))
    if limit is not None:
        return events[:limit]
    return events


def build_nvd_dataset(
    *,
    pub_start_date: str,
    pub_end_date: str,
    limit: int | None = None,
    api_key: str = "",
) -> list[dict[str, Any]]:
    params = {
        "pubStartDate": pub_start_date,
        "pubEndDate": pub_end_date,
        "resultsPerPage": str(min(limit or 2000, 2000)),
        "startIndex": "0",
    }
    headers = {}
    if api_key:
        headers["apiKey"] = api_key

    events: list[dict[str, Any]] = []
    while True:
        url = f"{NVD_API_URL}?{urllib.parse.urlencode(params)}"
        payload = _download_json(url, headers=headers)
        rows = payload.get("vulnerabilities", []) if isinstance(payload, dict) else []
        events.extend(_normalize_nvd(item) for item in rows if isinstance(item, dict))
        if limit is not None and len(events) >= limit:
            return events[:limit]
        total = int(payload.get("totalResults", len(events))) if isinstance(payload, dict) else len(events)
        start_index = int(params["startIndex"]) + len(rows)
        if not rows or start_index >= total:
            break
        params["startIndex"] = str(start_index)
    events.sort(key=lambda item: (item["timestamp"], item["event_id"]))
    return events


def write_dataset(
    events: Iterable[dict[str, Any]],
    output_dir: Path,
    *,
    dataset_id: str,
    source_urls: list[str] | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    event_list = list(events)
    events_path = output_dir / "events.jsonl"
    with events_path.open("w", encoding="utf-8") as handle:
        for item in event_list:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")

    manifest = {
        "dataset_id": dataset_id,
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_urls": source_urls or [CISA_KEV_URL],
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
    parser.add_argument("--source", choices=["cisa-kev", "nvd-api"], action="append", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dataset-id", default="cisa-kev")
    parser.add_argument("--nvd-pub-start", default="2024-01-01T00:00:00.000")
    parser.add_argument("--nvd-pub-end", default="2024-12-31T23:59:59.999")
    parser.add_argument("--nvd-api-key", default="")
    args = parser.parse_args(argv)

    sources = args.source or ["cisa-kev"]
    events: list[dict[str, Any]] = []
    source_urls: list[str] = []
    if "cisa-kev" in sources:
        events.extend(build_cisa_kev_dataset(limit=args.limit))
        source_urls.append(CISA_KEV_URL)
    if "nvd-api" in sources:
        events.extend(
            build_nvd_dataset(
                pub_start_date=args.nvd_pub_start,
                pub_end_date=args.nvd_pub_end,
                limit=args.limit,
                api_key=args.nvd_api_key,
            )
        )
        source_urls.append(NVD_API_URL)
    events = _dedupe_events(events)
    events.sort(key=lambda item: (item["timestamp"], item["event_id"]))
    if args.limit is not None and len(sources) == 1:
        events = events[: args.limit]
    manifest = write_dataset(events, args.out, dataset_id=args.dataset_id, source_urls=source_urls)
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
        "event_id": f"{cve_id.lower()}-cisa-kev",
        "source": "cisa_kev",
        "timestamp": f"{date_added}T00:00:00Z",
        "summary": " ".join(part for part in [title, summary] if part),
        "severity": 0.95,
        "tags": tags,
        "metadata": {
            "title": title,
            "cve_id": cve_id,
            "vendor": vendor,
            "product": product,
            "due_date": due_date,
            "required_action": item.get("requiredAction", ""),
            "known_ransomware_campaign_use": ransomware,
            "source_url": CISA_KEV_URL,
        },
    }


def _normalize_nvd(item: dict[str, Any]) -> dict[str, Any]:
    cve = item.get("cve", {}) if isinstance(item.get("cve"), dict) else {}
    cve_id = str(cve.get("id", "")).strip()
    descriptions = cve.get("descriptions", [])
    summary = ""
    for description in descriptions:
        if isinstance(description, dict) and description.get("lang") == "en":
            summary = str(description.get("value", "")).strip()
            break
    weaknesses = [
        str(desc.get("value"))
        for weakness in cve.get("weaknesses", [])
        if isinstance(weakness, dict)
        for desc in weakness.get("description", [])
        if isinstance(desc, dict) and desc.get("lang") == "en"
    ]
    score = _nvd_cvss_score(cve)
    tags = ["nvd"]
    tags.extend(item.lower() for item in weaknesses[:3])
    return {
        "event_id": f"{cve_id.lower()}-nvd",
        "source": "nvd",
        "timestamp": _nvd_timestamp(str(cve.get("published", ""))),
        "summary": summary or cve_id,
        "severity": round(score / 10, 3) if score is not None else 0.5,
        "tags": [tag for tag in tags if tag],
        "metadata": {
            "title": cve_id,
            "cve_id": cve_id,
            "vendor": "",
            "product": "",
            "cwe": weaknesses,
            "cvss_score": score,
            "source_url": NVD_API_URL,
        },
    }


def _download_json(url: str, *, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _tag(value: str) -> str:
    return "-".join(value.lower().replace("/", " ").replace("_", " ").split())


def _dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for event in events:
        event_id = str(event.get("event_id", ""))
        if not event_id or event_id in seen:
            continue
        seen.add(event_id)
        deduped.append(event)
    return deduped


def _nvd_timestamp(value: str) -> str:
    if not value:
        return "1970-01-01T00:00:00Z"
    if value.endswith("Z"):
        return value
    return f"{value}Z" if "T" in value else f"{value}T00:00:00Z"


def _nvd_cvss_score(cve: dict[str, Any]) -> float | None:
    metrics = cve.get("metrics", {}) if isinstance(cve.get("metrics"), dict) else {}
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        values = metrics.get(key)
        if not isinstance(values, list):
            continue
        for item in values:
            if not isinstance(item, dict):
                continue
            data = item.get("cvssData", {})
            if isinstance(data, dict) and data.get("baseScore") is not None:
                return float(data["baseScore"])
    return None


if __name__ == "__main__":
    raise SystemExit(main())
