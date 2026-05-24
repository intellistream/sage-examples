"""Describe a generated public demo dataset manifest."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .dataset_builder import read_jsonl


def describe_dataset(manifest_path: Path) -> dict[str, Any]:
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    events_path = Path(manifest["events_path"])
    events = read_jsonl(events_path)
    sources = Counter(str(item.get("source", "unknown")) for item in events)
    vendors = Counter(
        str((item.get("metadata") or {}).get("vendor", "unknown"))
        for item in events
        if isinstance(item.get("metadata"), dict)
    )
    tag_counts = Counter(tag for item in events for tag in item.get("tags", []))
    return {
        "dataset_id": manifest.get("dataset_id"),
        "record_count": len(events),
        "source_breakdown": dict(sources),
        "top_vendors": dict(vendors.most_common(10)),
        "top_tags": dict(tag_counts.most_common(15)),
        "events_path": str(events_path),
        "source_urls": manifest.get("source_urls", []),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(describe_dataset(args.manifest), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
