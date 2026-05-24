"""Run reproducible SageFlow demo experiments over real embedded records."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .adapter import InMemorySageFlowSnapshotAdapter
from .contracts import build_snapshot_contract, contract_allowed_evidence_ids, contract_evidence_ids
from .dataset_builder import read_jsonl
from .embeddings import EmbeddingCache
from .llm import generate_answer_from_contract
from .models import VectorStreamEvent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--embedding-cache", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--join-method", default="bruteforce_lazy")
    parser.add_argument("--window-size", type=int, action="append", default=None)
    parser.add_argument("--parallelism", type=int, action="append", default=None)
    parser.add_argument("--similarity-threshold", type=float, action="append", default=None)
    parser.add_argument("--generate-llm", action="store_true")
    parser.add_argument("--allow-template-fallback", action="store_true")
    args = parser.parse_args(argv)

    raw_events = read_jsonl(args.events)
    if args.limit is not None:
        raw_events = raw_events[: args.limit]
    cache = EmbeddingCache(args.embedding_cache)
    events = [_event_with_cached_embedding(item, cache) for item in raw_events]
    if not events:
        raise ValueError("experiment requires at least one event")

    window_sizes = args.window_size or [64]
    parallelism_values = args.parallelism or [1]
    thresholds = args.similarity_threshold or [0.85]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for window_size in window_sizes:
        for parallelism in parallelism_values:
            for threshold in thresholds:
                summary = _run_one_config(
                    events=events,
                    output_dir=args.out_dir,
                    join_method=args.join_method,
                    window_size=window_size,
                    parallelism=parallelism,
                    similarity_threshold=threshold,
                    generate_llm=args.generate_llm,
                    allow_template_fallback=args.allow_template_fallback,
                    embedding_cache_metadata=cache.metadata,
                )
                summaries.append(summary)

    summary_path = args.out_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump({"runs": summaries}, handle, ensure_ascii=False, indent=2, sort_keys=True)
    print(json.dumps({"summary_path": str(summary_path), "runs": summaries}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _run_one_config(
    *,
    events: list[VectorStreamEvent],
    output_dir: Path,
    join_method: str,
    window_size: int,
    parallelism: int,
    similarity_threshold: float,
    generate_llm: bool,
    allow_template_fallback: bool,
    embedding_cache_metadata: dict[str, Any],
) -> dict[str, Any]:
    run_id = (
        f"ws{window_size}-p{parallelism}-t{str(similarity_threshold).replace('.', '_')}"
        f"-{join_method}"
    )
    rows_path = output_dir / f"{run_id}.jsonl"
    adapter = InMemorySageFlowSnapshotAdapter(
        window_size=window_size,
        similarity_threshold=similarity_threshold,
        join_method=join_method,
        parallelism=parallelism,
    )
    rows: list[dict[str, Any]] = []
    event_by_id = {event.event_id: event for event in events}
    started_run = time.perf_counter()
    try:
        with rows_path.open("w", encoding="utf-8") as handle:
            for index, event in enumerate(events, start=1):
                row_started = time.perf_counter()
                join_started = time.perf_counter()
                response = adapter.process_event(event)
                join_ms = _elapsed_ms(join_started)

                contract_started = time.perf_counter()
                contract = build_snapshot_contract(response)
                contract_ms = _elapsed_ms(contract_started)

                answer = None
                llm_ms = None
                if generate_llm:
                    llm_started = time.perf_counter()
                    answer = generate_answer_from_contract(
                        contract,
                        allow_template_fallback=allow_template_fallback,
                    )
                    llm_ms = _elapsed_ms(llm_started)

                row = {
                    "run_id": run_id,
                    "event_index": index,
                    "event_id": event.event_id,
                    "embedding_dim": len(event.embedding),
                    "join_ms": join_ms,
                    "contract_ms": contract_ms,
                    "llm_ms": llm_ms,
                    "end_to_end_ms": _elapsed_ms(row_started),
                    "cluster_id": contract.cluster.cluster_id,
                    "cluster_size": contract.cluster.size,
                    "neighbor_count": len(contract.neighbors),
                    "evidence_ids": contract_evidence_ids(contract),
                    "runtime": contract.runtime.to_dict() if contract.runtime is not None else None,
                    "quality": _contract_quality(contract, event_by_id),
                    "llm": answer.to_dict() if answer is not None else None,
                    "faithfulness": _answer_faithfulness(answer.to_dict(), contract) if answer is not None else None,
                }
                rows.append(row)
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    finally:
        adapter.close()

    durations = [row["end_to_end_ms"] for row in rows]
    join_latencies = [row["join_ms"] for row in rows]
    llm_latencies = [row["llm_ms"] for row in rows if row["llm_ms"] is not None]
    quality_values = [
        row["quality"]["weak_label_purity"]
        for row in rows
        if row.get("quality") and row["quality"]["weak_label_purity"] is not None
    ]
    faithfulness_values = [
        row["faithfulness"]["cited_ids_are_contract_evidence"]
        for row in rows
        if row.get("faithfulness") and row["faithfulness"]["cited_ids_are_contract_evidence"] is not None
    ]
    wall_seconds = max(time.perf_counter() - started_run, 1e-9)
    return {
        "run_id": run_id,
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "rows_path": str(rows_path),
        "event_count": len(rows),
        "embedding_model": embedding_cache_metadata.get("model"),
        "embedding_dim": len(events[0].embedding),
        "join_method": join_method,
        "window_size": window_size,
        "parallelism": parallelism,
        "similarity_threshold": similarity_threshold,
        "throughput_events_per_sec": round(len(rows) / wall_seconds, 3),
        "end_to_end_p50_ms": _percentile(durations, 50),
        "end_to_end_p95_ms": _percentile(durations, 95),
        "join_p50_ms": _percentile(join_latencies, 50),
        "join_p95_ms": _percentile(join_latencies, 95),
        "llm_p50_ms": _percentile(llm_latencies, 50) if llm_latencies else None,
        "llm_p95_ms": _percentile(llm_latencies, 95) if llm_latencies else None,
        "avg_weak_label_purity": round(statistics.mean(quality_values), 4) if quality_values else None,
        "answer_evidence_faithfulness": round(statistics.mean(faithfulness_values), 4)
        if faithfulness_values
        else None,
        "generated_llm_answers": sum(1 for row in rows if row.get("llm") and row["llm"]["status"] == "generated"),
        "template_fallback_answers": sum(
            1 for row in rows if row.get("llm") and row["llm"]["status"] == "template_fallback"
        ),
        "llm_errors": sum(1 for row in rows if row.get("llm") and row["llm"].get("error")),
    }


def _event_with_cached_embedding(payload: dict[str, Any], cache: EmbeddingCache) -> VectorStreamEvent:
    event_id = str(payload.get("event_id", ""))
    embedding = cache.get(event_id)
    if embedding is None:
        raise ValueError(f"missing embedding for event_id={event_id!r}")
    enriched = dict(payload)
    metadata = dict(enriched.get("metadata", {}))
    metadata["embedding_cache"] = str(cache.path)
    metadata["embedding_cache_metadata"] = cache.metadata
    enriched["metadata"] = metadata
    enriched["embedding"] = embedding
    return VectorStreamEvent.from_dict(enriched)


def _contract_quality(contract: Any, event_by_id: dict[str, VectorStreamEvent]) -> dict[str, Any]:
    labels: list[str] = []
    for event_id in [contract.query_event.event_id, *contract.cluster.member_ids]:
        event = event_by_id.get(event_id)
        if event is None:
            continue
        labels.append(_weak_label(event))
    if not labels:
        return {"weak_label": None, "weak_label_purity": None}
    counts = Counter(labels)
    label, label_count = counts.most_common(1)[0]
    return {"weak_label": label, "weak_label_purity": round(label_count / len(labels), 4)}


def _answer_faithfulness(answer: dict[str, Any], contract: Any) -> dict[str, Any]:
    text = str(answer.get("answer", ""))
    contract_ids = set(contract_allowed_evidence_ids(contract, neighbor_limit=16))
    alias_to_contract_id = _contract_id_aliases(contract, contract_ids)
    if not text:
        return {
            "cited_event_ids": [],
            "cited_ids_are_contract_evidence": None,
            "cites_at_least_one_contract_id": False,
            "unsupported_event_like_ids": [],
        }

    candidate_ids = set(_extract_event_like_ids(text))
    if not candidate_ids:
        return {
            "cited_event_ids": [],
            "cited_ids_are_contract_evidence": None,
            "cites_at_least_one_contract_id": False,
            "unsupported_event_like_ids": [],
        }
    cited_ids: set[str] = set()
    unsupported: list[str] = []
    for candidate_id in candidate_ids:
        mapped = alias_to_contract_id.get(candidate_id.lower())
        if mapped is None:
            unsupported.append(candidate_id)
        else:
            cited_ids.add(mapped)
    return {
        "cited_event_ids": sorted(cited_ids),
        "unsupported_event_like_ids": sorted(unsupported),
        "cited_ids_are_contract_evidence": 1.0 if not unsupported else 0.0,
        "cites_at_least_one_contract_id": bool(cited_ids),
    }


def _contract_id_aliases(contract: Any, contract_ids: set[str]) -> dict[str, str]:
    aliases = {event_id.lower(): event_id for event_id in contract_ids}
    for item in [contract.query_event, *contract.neighbors]:
        event_id = str(getattr(item, "event_id", ""))
        if not event_id:
            continue
        aliases[event_id.lower()] = event_id
        metadata = getattr(item, "metadata", {}) or {}
        if isinstance(metadata, dict):
            for key in ("cve_id", "cve"):
                cve_id = metadata.get(key)
                if cve_id:
                    aliases[str(cve_id).lower()] = event_id
    return aliases


def _weak_label(event: VectorStreamEvent) -> str:
    vendor = str(event.metadata.get("vendor", "")).strip().lower()
    product = str(event.metadata.get("product", "")).strip().lower()
    if vendor or product:
        return "::".join(part for part in (vendor, product) if part)
    for tag in event.tags:
        if tag not in {"cisa-kev", "known-exploited"}:
            return tag
    return event.source


def _extract_event_like_ids(text: str) -> list[str]:
    return re.findall(r"\b(?:CVE|cve)-\d{4}-\d{4,7}(?:-[a-z0-9-]+)?\b", text)


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)


def _percentile(values: list[float], percentile: int) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return round(values[0], 3)
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile / 100
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return round(ordered[lower], 3)
    weight = rank - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 3)


if __name__ == "__main__":
    raise SystemExit(main())
