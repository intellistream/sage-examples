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

from .adapter import InMemorySageFlowSnapshotAdapter, _load_sage_flow_module, _stable_uid, _to_runtime_vector
from .config import apply_runtime_environment, experiment_config, load_demo_config, resolve_config_path
from .contracts import build_snapshot_contract, contract_allowed_evidence_ids, contract_evidence_ids
from .dataset_builder import read_jsonl
from .embeddings import EmbeddingCache
from .llm import generate_answer_from_contract
from .models import VectorStreamEvent

DEFAULT_RUNTIME_WINDOW_MS = 180 * 24 * 60 * 60 * 1000


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--experiment", default=None)
    parser.add_argument("--events", type=Path, default=None)
    parser.add_argument("--embedding-cache", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--join-method", action="append", default=None)
    parser.add_argument("--window-size", type=int, action="append", default=None)
    parser.add_argument("--parallelism", type=int, action="append", default=None)
    parser.add_argument("--similarity-threshold", type=float, action="append", default=None)
    parser.add_argument("--runtime-window-ms", type=int, default=None)
    parser.add_argument("--runtime-timestamp-mode", choices=("event_time", "sequence"), default=None)
    parser.add_argument("--runtime-event-interval-ms", type=int, default=None)
    parser.add_argument("--measurement-mode", choices=("service", "engine"), default=None)
    parser.add_argument("--generate-llm", action="store_true", default=None)
    parser.add_argument("--allow-template-fallback", action="store_true", default=None)
    args = parser.parse_args(argv)

    config, config_path = load_demo_config(args.config)
    apply_runtime_environment(config)
    _, selected_experiment = experiment_config(config, args.experiment)
    global_paths = config.get("paths") if isinstance(config.get("paths"), dict) else {}
    experiment_paths = selected_experiment.get("paths") if isinstance(selected_experiment.get("paths"), dict) else {}
    paths = {**global_paths, **experiment_paths}

    events_path = args.events or resolve_config_path(paths.get("events"), config_path)
    embedding_cache_path = args.embedding_cache or resolve_config_path(paths.get("embedding_cache"), config_path)
    output_dir = args.out_dir or resolve_config_path(selected_experiment.get("output_dir"), config_path)
    if events_path is None:
        parser.error("--events is required when the config has no paths.events")
    if embedding_cache_path is None:
        parser.error("--embedding-cache is required when the config has no paths.embedding_cache")
    if output_dir is None:
        parser.error("--out-dir is required when the selected config experiment has no output_dir")

    limit = _coalesce(args.limit, selected_experiment.get("limit"))
    raw_events = read_jsonl(events_path)
    if limit is not None:
        raw_events = raw_events[: int(limit)]
    cache = EmbeddingCache(embedding_cache_path)
    events = [_event_with_cached_embedding(item, cache) for item in raw_events]
    if not events:
        raise ValueError("experiment requires at least one event")

    window_sizes = args.window_size or _int_list(selected_experiment.get("window_sizes"), [64])
    parallelism_values = args.parallelism or _int_list(selected_experiment.get("parallelism"), [1])
    thresholds = args.similarity_threshold or _float_list(selected_experiment.get("similarity_thresholds"), [0.85])
    join_methods = args.join_method or _str_list(
        selected_experiment.get("join_methods", selected_experiment.get("join_method")),
        ["bruteforce_lazy"],
    )
    runtime_window_ms = _coalesce(args.runtime_window_ms, selected_experiment.get("runtime_window_ms"))
    runtime_timestamp_mode = str(
        _coalesce(args.runtime_timestamp_mode, selected_experiment.get("runtime_timestamp_mode", "event_time"))
    )
    runtime_event_interval_ms = int(
        _coalesce(args.runtime_event_interval_ms, selected_experiment.get("runtime_event_interval_ms", 10))
    )
    measurement_mode = str(_coalesce(args.measurement_mode, selected_experiment.get("measurement_mode", "service")))
    queue_capacity = int(selected_experiment.get("queue_capacity", max(4096, len(events) * 2 + 16)))
    clustered_multicast_k = int(selected_experiment.get("clustered_multicast_k", 0))
    clustered_overlap_ratio = float(selected_experiment.get("clustered_overlap_ratio", 0.1))
    clustered_training_samples = int(selected_experiment.get("clustered_training_samples", 1000))
    clustered_index_type = str(selected_experiment.get("clustered_index_type", "bruteforce"))
    generate_llm = _bool_coalesce(args.generate_llm, selected_experiment.get("generate_llm"), False)
    allow_template_fallback = _bool_coalesce(
        args.allow_template_fallback,
        selected_experiment.get("allow_template_fallback"),
        False,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for join_method in join_methods:
        for window_size in window_sizes:
            for parallelism in parallelism_values:
                for threshold in thresholds:
                    run_args = dict(
                        events=events,
                        output_dir=output_dir,
                        join_method=join_method,
                        window_size=window_size,
                        parallelism=parallelism,
                        similarity_threshold=threshold,
                        runtime_window_ms=runtime_window_ms,
                        runtime_timestamp_mode=runtime_timestamp_mode,
                        runtime_event_interval_ms=runtime_event_interval_ms,
                        embedding_cache_metadata=cache.metadata,
                    )
                    if measurement_mode == "engine":
                        summary = _run_engine_config(
                            queue_capacity=queue_capacity,
                            clustered_multicast_k=clustered_multicast_k,
                            clustered_overlap_ratio=clustered_overlap_ratio,
                            clustered_training_samples=clustered_training_samples,
                            clustered_index_type=clustered_index_type,
                            **run_args,
                        )
                    else:
                        summary = _run_one_config(
                            generate_llm=generate_llm,
                            allow_template_fallback=allow_template_fallback,
                            **run_args,
                        )
                    summaries.append(summary)

    summary_path = output_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump({"runs": summaries}, handle, ensure_ascii=False, indent=2, sort_keys=True)
    print(json.dumps({"summary_path": str(summary_path), "runs": summaries}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _coalesce(primary: Any, fallback: Any) -> Any:
    return primary if primary is not None else fallback


def _bool_coalesce(primary: bool | None, fallback: Any, default: bool) -> bool:
    if primary is not None:
        return bool(primary)
    if fallback is None:
        return default
    return bool(fallback)


def _int_list(value: Any, default: list[int]) -> list[int]:
    if value is None:
        return default
    if isinstance(value, list):
        return [int(item) for item in value]
    return [int(value)]


def _float_list(value: Any, default: list[float]) -> list[float]:
    if value is None:
        return default
    if isinstance(value, list):
        return [float(item) for item in value]
    return [float(value)]


def _str_list(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return default
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _run_one_config(
    *,
    events: list[VectorStreamEvent],
    output_dir: Path,
    join_method: str,
    window_size: int,
    parallelism: int,
    similarity_threshold: float,
    runtime_window_ms: Any,
    runtime_timestamp_mode: str,
    runtime_event_interval_ms: int,
    generate_llm: bool,
    allow_template_fallback: bool,
    embedding_cache_metadata: dict[str, Any],
) -> dict[str, Any]:
    effective_runtime_window_ms = _runtime_window_ms_for_config(
        runtime_window_ms=runtime_window_ms,
        runtime_timestamp_mode=runtime_timestamp_mode,
        runtime_event_interval_ms=runtime_event_interval_ms,
        window_size=window_size,
    )
    run_id = (
        f"ws{window_size}-p{parallelism}-t{str(similarity_threshold).replace('.', '_')}"
        f"-{join_method}"
    )
    rows_path = output_dir / f"{run_id}.jsonl"
    adapter = InMemorySageFlowSnapshotAdapter(
        window_size=window_size,
        similarity_threshold=similarity_threshold,
        join_method=join_method,
        runtime_window_ms=effective_runtime_window_ms,
        runtime_timestamp_mode=runtime_timestamp_mode,
        runtime_event_interval_ms=runtime_event_interval_ms,
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
                    "runtime_timestamp_mode": runtime_timestamp_mode,
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
        "measurement_mode": "service",
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "rows_path": str(rows_path),
        "event_count": len(rows),
        "embedding_model": embedding_cache_metadata.get("model"),
        "embedding_dim": len(events[0].embedding),
        "join_method": join_method,
        "window_size": window_size,
        "runtime_window_ms": effective_runtime_window_ms,
        "runtime_timestamp_mode": runtime_timestamp_mode,
        "runtime_event_interval_ms": runtime_event_interval_ms,
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


def _run_engine_config(
    *,
    events: list[VectorStreamEvent],
    output_dir: Path,
    join_method: str,
    window_size: int,
    parallelism: int,
    similarity_threshold: float,
    runtime_window_ms: Any,
    runtime_timestamp_mode: str,
    runtime_event_interval_ms: int,
    embedding_cache_metadata: dict[str, Any],
    queue_capacity: int,
    clustered_multicast_k: int,
    clustered_overlap_ratio: float,
    clustered_training_samples: int,
    clustered_index_type: str,
) -> dict[str, Any]:
    effective_runtime_window_ms = _runtime_window_ms_for_config(
        runtime_window_ms=runtime_window_ms,
        runtime_timestamp_mode=runtime_timestamp_mode,
        runtime_event_interval_ms=runtime_event_interval_ms,
        window_size=window_size,
    )
    run_id = (
        f"ws{window_size}-p{parallelism}-t{str(similarity_threshold).replace('.', '_')}"
        f"-{join_method}-engine"
    )
    rows_path = output_dir / f"{run_id}.json"
    dim = max(len(events[0].embedding), 16)
    prepared_records = [
        (
            _stable_uid(event.event_id),
            _runtime_timestamp_for_index(event, index, runtime_timestamp_mode, runtime_event_interval_ms),
            _to_runtime_vector(event.embedding, dim),
        )
        for index, event in enumerate(events)
    ]
    sage_flow = _load_sage_flow_module()
    runtime = sage_flow.PersistentVectorJoinRuntime(
        dim,
        join_method,
        similarity_threshold,
        effective_runtime_window_ms,
        queue_capacity,
        parallelism,
        clustered_multicast_k,
        clustered_overlap_ratio,
        clustered_training_samples,
        clustered_index_type,
    )

    startup_started = time.perf_counter()
    runtime.start()
    startup_ms = _elapsed_ms(startup_started)

    feed_started = time.perf_counter()
    try:
        for uid, timestamp_ms, vector in prepared_records:
            runtime.add_right(uid, timestamp_ms, vector)
            runtime.add_left(uid, timestamp_ms, vector)
        runtime_info_before_close = runtime.runtime_info()
    finally:
        runtime.close()
    feed_and_drain_seconds = max(time.perf_counter() - feed_started, 1e-9)
    emitted_pairs = int(runtime.emitted_pair_count())

    summary = {
        "run_id": run_id,
        "measurement_mode": "engine",
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "rows_path": str(rows_path),
        "event_count": len(events),
        "vector_insert_count": len(events) * 2,
        "embedding_model": embedding_cache_metadata.get("model"),
        "embedding_dim": dim,
        "join_method": join_method,
        "window_size": window_size,
        "runtime_window_ms": effective_runtime_window_ms,
        "runtime_timestamp_mode": runtime_timestamp_mode,
        "runtime_event_interval_ms": runtime_event_interval_ms,
        "parallelism": parallelism,
        "similarity_threshold": similarity_threshold,
        "queue_capacity": queue_capacity,
        "clustered_multicast_k": clustered_multicast_k if _is_clustered_join(join_method) else None,
        "clustered_overlap_ratio": clustered_overlap_ratio if _is_clustered_join(join_method) else None,
        "clustered_training_samples": clustered_training_samples if _is_clustered_join(join_method) else None,
        "clustered_index_type": clustered_index_type if _is_clustered_join(join_method) else None,
        "startup_ms": startup_ms,
        "feed_and_drain_ms": round(feed_and_drain_seconds * 1000, 3),
        "throughput_events_per_sec": round(len(events) / feed_and_drain_seconds, 3),
        "throughput_vectors_per_sec": round((len(events) * 2) / feed_and_drain_seconds, 3),
        "emitted_pairs": emitted_pairs,
        "runtime_info_before_close": dict(runtime_info_before_close),
    }
    rows_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def _is_clustered_join(join_method: str) -> bool:
    normalized = join_method.lower()
    return normalized in {"clustered_join", "clusteredjoin", "clustered_join_eager", "clustered_join_lazy"}


def _runtime_timestamp_for_index(
    event: VectorStreamEvent,
    index: int,
    runtime_timestamp_mode: str,
    runtime_event_interval_ms: int,
) -> int:
    if runtime_timestamp_mode == "event_time":
        normalized = event.timestamp.replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(normalized)
        return int(parsed.timestamp() * 1000)
    return index * runtime_event_interval_ms


def _runtime_window_ms_for_config(
    *,
    runtime_window_ms: Any,
    runtime_timestamp_mode: str,
    runtime_event_interval_ms: int,
    window_size: int,
) -> int:
    if runtime_window_ms is not None:
        return int(runtime_window_ms)
    if runtime_timestamp_mode == "sequence":
        return max(int(window_size) * int(runtime_event_interval_ms), int(runtime_event_interval_ms))
    return DEFAULT_RUNTIME_WINDOW_MS


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
