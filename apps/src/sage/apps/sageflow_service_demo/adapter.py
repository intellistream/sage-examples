"""Persistent SageFlow runtime adapter for the ICPP service demo."""

from __future__ import annotations

import datetime as dt
import importlib
import math
import threading
import time
import zlib
from collections import Counter
from typing import Literal

import numpy as np

from .models import (
    ClusterSnapshot,
    NearestNeighbor,
    SageFlowRuntimeInfo,
    SageFlowServiceResponse,
    SageFlowWindowSnapshot,
    VectorStreamEvent,
    coerce_vector_stream_event,
)

Side = Literal["left", "right"]


def _load_sage_flow_module():
    try:
        return importlib.import_module("sage_flow")
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "sage_flow is required for this demo. Install isage-flow or add the sageFlow "
            "repository to PYTHONPATH before running the example."
        ) from exc


class InMemorySageFlowSnapshotAdapter:
    """Long-lived adapter backed by SageFlow's persistent streaming join runtime.

    The adapter owns one SageFlow ``PersistentVectorJoinRuntime`` for its whole
    lifetime. Records are appended to StreamingSource inputs, while the SAGE
    service boundary reads emitted join pairs and folds them into application
    contracts.
    """

    def __init__(
        self,
        *,
        window_size: int = 16,
        similarity_threshold: float = 0.985,
        max_neighbors: int = 3,
        queue_capacity: int = 1024,
        join_method: str = "bruteforce_lazy",
        runtime_window_ms: int = 180 * 24 * 60 * 60 * 1000,
        parallelism: int = 1,
    ) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if not 0.0 < similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be in (0, 1]")
        if max_neighbors <= 0:
            raise ValueError("max_neighbors must be positive")
        if queue_capacity <= 0:
            raise ValueError("queue_capacity must be positive")
        if runtime_window_ms <= 0:
            raise ValueError("runtime_window_ms must be positive")
        if not join_method:
            raise ValueError("join_method must be non-empty")

        self.window_size = window_size
        self.similarity_threshold = similarity_threshold
        self.max_neighbors = max_neighbors
        self.queue_capacity = queue_capacity
        self.join_method = join_method
        self.runtime_window_ms = runtime_window_ms
        self.parallelism = parallelism

        self._latest_snapshot: SageFlowWindowSnapshot | None = None
        self._active_events: list[VectorStreamEvent] = []
        self._event_by_uid: dict[int, VectorStreamEvent] = {}
        self._join_pairs: list[tuple[int, int, float]] = []
        self._lock = threading.RLock()
        self._sage_flow = _load_sage_flow_module()
        self._runtime = None
        self._runtime_dim: int | None = None
        self._seen_right_uids: set[int] = set()
        self._seen_left_uids: set[int] = set()

    def reset(self) -> None:
        with self._lock:
            if self._runtime is not None:
                self._runtime.close()
            self._runtime = None
            self._runtime_dim = None
            self._latest_snapshot = None
            self._active_events.clear()
            self._event_by_uid.clear()
            self._join_pairs.clear()
            self._seen_right_uids.clear()
            self._seen_left_uids.clear()

    def process_event(
        self,
        event: VectorStreamEvent | dict[str, object],
    ) -> SageFlowServiceResponse:
        resolved = coerce_vector_stream_event(event)
        with self._lock:
            return self._process_locked(resolved, side="left", mirror_to_right=True)

    def process_dual_source_event(
        self,
        event: VectorStreamEvent | dict[str, object],
        *,
        side: Side,
    ) -> SageFlowServiceResponse:
        if side not in {"left", "right"}:
            raise ValueError("side must be 'left' or 'right'")
        resolved = coerce_vector_stream_event(event)
        with self._lock:
            return self._process_locked(resolved, side=side, mirror_to_right=(side == "left"))

    def get_latest_snapshot(self) -> SageFlowWindowSnapshot | None:
        return self._latest_snapshot

    def runtime_info(self) -> SageFlowRuntimeInfo:
        with self._lock:
            if self._runtime is None:
                return SageFlowRuntimeInfo(
                    mode="not_started",
                    join_method=self.join_method,
                    similarity_threshold=self.similarity_threshold,
                    window_size_ms=self.runtime_window_ms,
                    parallelism=self.parallelism,
                    retained_left_records=0,
                    retained_right_records=0,
                    queued_left_records=0,
                    queued_right_records=0,
                    emitted_pairs=0,
                )

            payload = self._runtime.runtime_info()
            return SageFlowRuntimeInfo(
                mode=str(payload["mode"]),
                join_method=str(payload["join_method"]),
                similarity_threshold=float(payload["similarity_threshold"]),
                window_size_ms=int(payload["window_size_ms"]),
                parallelism=int(payload["parallelism"]),
                retained_left_records=int(payload["retained_left_records"]),
                retained_right_records=int(payload["retained_right_records"]),
                queued_left_records=int(payload["queued_left_records"]),
                queued_right_records=int(payload["queued_right_records"]),
                emitted_pairs=int(payload["emitted_pairs"]),
            )

    def close(self) -> None:
        with self._lock:
            if self._runtime is not None:
                self._runtime.close()
                self._runtime = None

    def _process_locked(
        self,
        event: VectorStreamEvent,
        *,
        side: Side,
        mirror_to_right: bool,
    ) -> SageFlowServiceResponse:
        self._ensure_runtime_locked(event)

        uid = _stable_uid(event.event_id)
        self._event_by_uid[uid] = event
        self._upsert_active_event_locked(event)

        cursor = self._runtime.emitted_pair_count()
        if side == "right":
            self._add_right_locked(uid, event)
            self._add_left_locked(uid, event)
        else:
            if mirror_to_right:
                self._add_right_locked(uid, event)
            self._add_left_locked(uid, event)

        self._runtime.wait_for_pair_count(cursor + 1, 50)
        time.sleep(0.005)
        self._drain_pairs_locked()

        active_uids = {_stable_uid(item.event_id) for item in self._active_events}
        active_pairs = [
            pair for pair in self._join_pairs
            if pair[0] in active_uids and pair[1] in active_uids
        ]
        clusters = self._build_components_from_join_pairs(self._active_events, active_pairs)
        active_cluster = next(
            cluster for cluster in clusters if any(record.event_id == event.event_id for record in cluster)
        )
        nearest_neighbors = self._nearest_neighbors_for_event(event, active_pairs)
        top_similarity = nearest_neighbors[0].similarity if nearest_neighbors else 0.0
        novelty_score = round(1.0 - top_similarity, 4)
        window_snapshot = self._build_window_snapshot(event.timestamp, event.event_id, clusters)
        self._latest_snapshot = window_snapshot

        return SageFlowServiceResponse(
            event=event,
            active_cluster=self._to_cluster_snapshot(active_cluster, clusters.index(active_cluster)),
            novelty_score=novelty_score,
            nearest_neighbors=nearest_neighbors,
            window_snapshot=window_snapshot,
        )

    def _ensure_runtime_locked(self, event: VectorStreamEvent) -> None:
        runtime_dim = max(len(event.embedding), 16)
        if self._runtime is not None:
            if runtime_dim != self._runtime_dim:
                raise ValueError("all embeddings must share the same dimensionality")
            return

        self._runtime_dim = runtime_dim
        self._runtime = self._sage_flow.PersistentVectorJoinRuntime(
            runtime_dim,
            self.join_method,
            self.similarity_threshold,
            self.runtime_window_ms,
            self.queue_capacity,
            self.parallelism,
        )
        self._runtime.start()

    def _add_left_locked(self, uid: int, event: VectorStreamEvent) -> None:
        if uid in self._seen_left_uids:
            return
        self._runtime.add_left(uid, _timestamp_to_epoch_millis(event.timestamp), _to_runtime_vector(event.embedding, self._runtime_dim or 16))
        self._seen_left_uids.add(uid)

    def _add_right_locked(self, uid: int, event: VectorStreamEvent) -> None:
        if uid in self._seen_right_uids:
            return
        self._runtime.add_right(uid, _timestamp_to_epoch_millis(event.timestamp), _to_runtime_vector(event.embedding, self._runtime_dim or 16))
        self._seen_right_uids.add(uid)

    def _upsert_active_event_locked(self, event: VectorStreamEvent) -> None:
        self._active_events = [item for item in self._active_events if item.event_id != event.event_id]
        self._active_events.append(event)
        self._active_events = self._active_events[-self.window_size :]

    def _drain_pairs_locked(self) -> None:
        if self._runtime is None:
            return
        cursor = len(self._join_pairs)
        for pair in self._runtime.pairs_since(cursor):
            left_uid = int(pair.left_uid)
            right_uid = int(pair.right_uid)
            if left_uid == right_uid:
                continue
            key = tuple(sorted((left_uid, right_uid)))
            similarity = float(pair.similarity)
            if not any(tuple(sorted((existing[0], existing[1]))) == key for existing in self._join_pairs):
                self._join_pairs.append((left_uid, right_uid, similarity))

    def _nearest_neighbors_for_event(
        self,
        event: VectorStreamEvent,
        join_pairs: list[tuple[int, int, float]],
    ) -> list[NearestNeighbor]:
        uid = _stable_uid(event.event_id)
        neighbors: list[NearestNeighbor] = []
        for left_uid, right_uid, similarity in join_pairs:
            if left_uid == uid:
                neighbor_uid = right_uid
            elif right_uid == uid:
                neighbor_uid = left_uid
            else:
                continue
            candidate = self._event_by_uid.get(neighbor_uid)
            if candidate is None or candidate.event_id == event.event_id:
                continue
            neighbors.append(
                NearestNeighbor(
                    event_id=candidate.event_id,
                    source=candidate.source,
                    similarity=round(similarity, 4),
                    summary=candidate.summary,
                )
            )
        neighbors.sort(key=lambda item: item.similarity, reverse=True)
        return neighbors[: self.max_neighbors]

    def _build_window_snapshot(
        self,
        generated_at: str,
        latest_event_id: str,
        clusters: list[list[VectorStreamEvent]],
    ) -> SageFlowWindowSnapshot:
        active_events = [record for cluster in clusters for record in cluster]
        source_counter = Counter(record.source for record in active_events)
        hot_clusters = [
            self._to_cluster_snapshot(cluster, index)
            for index, cluster in sorted(
                enumerate(clusters),
                key=lambda item: (-len(item[1]), -_average_severity(item[1]), item[0]),
            )
        ]
        return SageFlowWindowSnapshot(
            generated_at=generated_at,
            window_size=len(active_events),
            cluster_count=len(clusters),
            latest_event_id=latest_event_id,
            hot_clusters=hot_clusters,
            source_breakdown=dict(source_counter),
        )

    def _to_cluster_snapshot(
        self,
        cluster: list[VectorStreamEvent],
        cluster_index: int,
    ) -> ClusterSnapshot:
        source_counter = Counter(record.source for record in cluster)
        tag_counter = Counter(tag for record in cluster for tag in record.tags)
        top_tags = [tag for tag, _ in tag_counter.most_common(3)]
        return ClusterSnapshot(
            cluster_id=f"cluster-{cluster_index + 1}",
            size=len(cluster),
            average_severity=round(_average_severity(cluster), 4),
            member_ids=[record.event_id for record in cluster],
            top_tags=top_tags,
            source_breakdown=dict(source_counter),
        )

    def _build_components_from_join_pairs(
        self,
        records: list[VectorStreamEvent],
        join_pairs: list[tuple[int, int, float]],
    ) -> list[list[VectorStreamEvent]]:
        if not records:
            return []

        adjacency = {index: set() for index in range(len(records))}
        index_by_uid = {_stable_uid(record.event_id): index for index, record in enumerate(records)}

        for left_uid, right_uid, _ in join_pairs:
            left_index = index_by_uid.get(left_uid)
            right_index = index_by_uid.get(right_uid)
            if left_index is None or right_index is None:
                continue
            adjacency[left_index].add(right_index)
            adjacency[right_index].add(left_index)

        components: list[list[VectorStreamEvent]] = []
        visited: set[int] = set()
        for index in range(len(records)):
            if index in visited:
                continue
            stack = [index]
            component_indexes: list[int] = []
            visited.add(index)
            while stack:
                current = stack.pop()
                component_indexes.append(current)
                for neighbor in adjacency[current]:
                    if neighbor in visited:
                        continue
                    visited.add(neighbor)
                    stack.append(neighbor)

            component_indexes.sort()
            components.append([records[item] for item in component_indexes])

        components.sort(key=lambda cluster: cluster[0].timestamp)
        return components


def _average_severity(records: list[VectorStreamEvent]) -> float:
    return sum(record.severity for record in records) / max(len(records), 1)


def _stable_uid(event_id: str) -> int:
    return zlib.crc32(event_id.encode("utf-8"))


def _timestamp_to_epoch_millis(timestamp: str) -> int:
    normalized = timestamp.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    return int(parsed.timestamp() * 1000)


def _to_runtime_vector(embedding: tuple[float, ...], dimension: int) -> np.ndarray:
    vector = np.zeros(dimension, dtype=np.float32)
    vector[: len(embedding)] = np.asarray(embedding, dtype=np.float32)
    return vector
