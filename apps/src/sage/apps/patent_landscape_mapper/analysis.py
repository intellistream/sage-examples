"""Patent landscape analysis logic."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from math import ceil
from re import sub

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import (
    LandscapeGraphEdge,
    LandscapeGraphNode,
    PatentLandscapeReport,
    PatentLandscapeRequest,
    PatentRecord,
    PatentWatchItem,
    ThemeCluster,
    WhiteSpaceOpportunity,
)


@dataclass(frozen=True)
class _ClusterState:
    cluster_id: int
    patent_indexes: list[int]
    label: str
    top_terms: list[str]
    representative_indexes: list[int]
    assignee_breakdown: dict[str, int]
    average_focus_relevance: float
    whitespace_score: float


def _slugify(value: str) -> str:
    normalized = sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "node"


def _build_document(record: PatentRecord) -> str:
    return " ".join([record.title, record.abstract, " ".join(record.tags), record.assignee])


def _normalize_cluster_count(requested: int, patent_count: int) -> int:
    if patent_count < 2:
        raise ValueError("Patent landscape mapping requires at least two patent records.")
    return max(2, min(requested, patent_count))


def _clean_term(term: str) -> str:
    return term.replace("_", " ").strip()


def _derive_cluster_label(records: list[PatentRecord], top_terms: list[str]) -> str:
    tag_counter: Counter[str] = Counter()
    for record in records:
        tag_counter.update(record.tags)
    ranked_tags = [tag for tag, _ in tag_counter.most_common(2)]
    if ranked_tags:
        return " / ".join(tag.title() for tag in ranked_tags)
    return " / ".join(term.title() for term in top_terms[:2])


def _top_terms_from_centroid(
    centroid: np.ndarray,
    feature_names: np.ndarray,
    top_k: int,
) -> list[str]:
    ranked_indexes = np.argsort(centroid)[::-1]
    terms: list[str] = []
    for index in ranked_indexes:
        term = _clean_term(str(feature_names[index]))
        if term and term not in terms:
            terms.append(term)
        if len(terms) >= top_k:
            break
    return terms


def _focus_scores(
    matrix: np.ndarray,
    vectorizer: TfidfVectorizer,
    focus_keywords: list[str],
) -> np.ndarray:
    if not focus_keywords:
        return np.full(shape=(matrix.shape[0],), fill_value=0.5, dtype=float)
    keyword_matrix = vectorizer.transform(focus_keywords)
    return cosine_similarity(matrix, keyword_matrix).max(axis=1)


def _build_clusters(
    request: PatentLandscapeRequest,
    patents: list[PatentRecord],
    matrix: np.ndarray,
    feature_names: np.ndarray,
    assignments: np.ndarray,
    centroids: np.ndarray,
    focus_scores: np.ndarray,
) -> list[_ClusterState]:
    index_groups: dict[int, list[int]] = defaultdict(list)
    for index, cluster_id in enumerate(assignments.tolist()):
        index_groups[int(cluster_id)].append(index)

    largest_cluster_size = max(len(indexes) for indexes in index_groups.values())
    states: list[_ClusterState] = []

    for cluster_id, patent_indexes in sorted(index_groups.items()):
        cluster_patents = [patents[index] for index in patent_indexes]
        centroid = centroids[cluster_id]
        top_terms = _top_terms_from_centroid(centroid, feature_names, request.top_terms_per_cluster)
        label = _derive_cluster_label(cluster_patents, top_terms)

        local_matrix = matrix[patent_indexes]
        similarities = cosine_similarity(local_matrix, centroid.reshape(1, -1)).reshape(-1)
        representative_local_indexes = np.argsort(similarities)[::-1][
            : request.top_patents_per_cluster
        ]
        representative_indexes = [
            patent_indexes[index] for index in representative_local_indexes.tolist()
        ]

        assignee_breakdown = dict(Counter(record.assignee for record in cluster_patents))
        top_assignee_share = max(assignee_breakdown.values()) / len(cluster_patents)
        density = len(cluster_patents) / largest_cluster_size
        sparsity = 1.0 - density
        fragmentation = 1.0 - top_assignee_share
        average_focus_relevance = float(np.mean(focus_scores[patent_indexes]))
        focus_alignment = average_focus_relevance if request.focus_keywords else 0.5
        whitespace_score = round(
            min(1.0, 0.45 * focus_alignment + 0.35 * sparsity + 0.20 * fragmentation),
            3,
        )

        states.append(
            _ClusterState(
                cluster_id=cluster_id,
                patent_indexes=patent_indexes,
                label=label,
                top_terms=top_terms,
                representative_indexes=representative_indexes,
                assignee_breakdown=assignee_breakdown,
                average_focus_relevance=round(average_focus_relevance, 3),
                whitespace_score=whitespace_score,
            )
        )

    return sorted(states, key=lambda item: item.whitespace_score, reverse=True)


def _build_theme_clusters(
    states: list[_ClusterState], patents: list[PatentRecord]
) -> list[ThemeCluster]:
    return [
        ThemeCluster(
            cluster_id=state.cluster_id,
            label=state.label,
            top_terms=state.top_terms,
            patent_ids=[patents[index].patent_id for index in state.patent_indexes],
            patent_count=len(state.patent_indexes),
            representative_patent_ids=[
                patents[index].patent_id for index in state.representative_indexes
            ],
            assignee_breakdown=state.assignee_breakdown,
            average_focus_relevance=state.average_focus_relevance,
            whitespace_score=state.whitespace_score,
        )
        for state in states
    ]


def _build_whitespace_opportunities(
    states: list[_ClusterState],
    patents: list[PatentRecord],
) -> list[WhiteSpaceOpportunity]:
    opportunities: list[WhiteSpaceOpportunity] = []
    for state in states[:3]:
        top_assignee, top_assignee_count = max(
            state.assignee_breakdown.items(),
            key=lambda item: item[1],
        )
        patent_count = len(state.patent_indexes)
        rationale = (
            f"Theme '{state.label}' has {patent_count} patents in the demo corpus, while the leading "
            f"assignee '{top_assignee}' controls only {top_assignee_count}/{patent_count}. That leaves "
            "room for differentiated products, especially around the cluster's strongest technical terms."
        )
        opportunities.append(
            WhiteSpaceOpportunity(
                cluster_id=state.cluster_id,
                title=f"Expand into {state.label}",
                rationale=rationale,
                target_keywords=state.top_terms[:3],
                opportunity_score=state.whitespace_score,
                supporting_patent_ids=[
                    patents[index].patent_id for index in state.representative_indexes
                ],
            )
        )
    return opportunities


def _build_watchlist(
    states: list[_ClusterState],
    patents: list[PatentRecord],
    focus_scores: np.ndarray,
) -> list[PatentWatchItem]:
    cluster_lookup = {state.cluster_id: state for state in states}
    min_year = min(record.year for record in patents)
    max_year = max(record.year for record in patents)
    year_span = max(1, max_year - min_year)

    watch_items: list[PatentWatchItem] = []
    for state in states:
        for index in state.patent_indexes:
            record = patents[index]
            recency_score = (record.year - min_year) / year_span
            watch_score = round(
                0.55 * float(focus_scores[index])
                + 0.30 * state.whitespace_score
                + 0.15 * recency_score,
                3,
            )
            watch_items.append(
                PatentWatchItem(
                    patent_id=record.patent_id,
                    title=record.title,
                    assignee=record.assignee,
                    theme_label=cluster_lookup[state.cluster_id].label,
                    watch_score=watch_score,
                    focus_relevance=round(float(focus_scores[index]), 3),
                    reason=(
                        "High strategic relevance combined with an under-concentrated theme cluster and "
                        "recent filing activity."
                    ),
                )
            )
    return sorted(watch_items, key=lambda item: item.watch_score, reverse=True)[:5]


def _build_graph(
    states: list[_ClusterState], patents: list[PatentRecord]
) -> tuple[list[LandscapeGraphNode], list[LandscapeGraphEdge]]:
    nodes: list[LandscapeGraphNode] = []
    edges: list[LandscapeGraphEdge] = []
    seen_assignees: set[str] = set()

    for state in states:
        theme_node_id = f"theme:{state.cluster_id}"
        nodes.append(
            LandscapeGraphNode(
                node_id=theme_node_id,
                node_type="theme",
                label=state.label,
                attributes={
                    "whitespace_score": state.whitespace_score,
                    "average_focus_relevance": state.average_focus_relevance,
                },
            )
        )
        for index in state.patent_indexes:
            record = patents[index]
            patent_node_id = f"patent:{record.patent_id}"
            nodes.append(
                LandscapeGraphNode(
                    node_id=patent_node_id,
                    node_type="patent",
                    label=record.title,
                    attributes={"assignee": record.assignee, "year": record.year},
                )
            )
            edges.append(
                LandscapeGraphEdge(
                    source_id=patent_node_id,
                    target_id=theme_node_id,
                    relation="maps_to_theme",
                )
            )

            assignee_node_id = f"assignee:{_slugify(record.assignee)}"
            if assignee_node_id not in seen_assignees:
                nodes.append(
                    LandscapeGraphNode(
                        node_id=assignee_node_id,
                        node_type="assignee",
                        label=record.assignee,
                    )
                )
                seen_assignees.add(assignee_node_id)
            edges.append(
                LandscapeGraphEdge(
                    source_id=assignee_node_id,
                    target_id=patent_node_id,
                    relation="owns_patent",
                )
            )

    return nodes, edges


def analyze_patent_landscape(request: PatentLandscapeRequest) -> PatentLandscapeReport:
    cluster_count = _normalize_cluster_count(request.cluster_count, len(request.patents))
    patents = list(request.patents)
    documents = [_build_document(record) for record in patents]

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)
    sparse_matrix = vectorizer.fit_transform(documents)
    dense_matrix = sparse_matrix.toarray()
    feature_names = vectorizer.get_feature_names_out()

    estimator = KMeans(n_clusters=cluster_count, random_state=42, n_init=20)
    assignments = estimator.fit_predict(sparse_matrix)
    focus_scores = _focus_scores(sparse_matrix, vectorizer, request.focus_keywords)

    states = _build_clusters(
        request=request,
        patents=patents,
        matrix=dense_matrix,
        feature_names=feature_names,
        assignments=assignments,
        centroids=estimator.cluster_centers_,
        focus_scores=focus_scores,
    )
    theme_clusters = _build_theme_clusters(states, patents)
    whitespace_opportunities = _build_whitespace_opportunities(states, patents)
    watchlist_patents = _build_watchlist(states, patents, focus_scores)
    graph_nodes, graph_edges = _build_graph(states, patents)

    top_themes = ", ".join(
        cluster.label for cluster in theme_clusters[: min(ceil(cluster_count / 2), 3)]
    )
    lead_opportunity = (
        whitespace_opportunities[0].title
        if whitespace_opportunities
        else "No whitespace opportunity identified"
    )
    summary = (
        f"Mapped {len(patents)} patents across {cluster_count} themes. Leading themes: {top_themes}. "
        f"Top whitespace opportunity: {lead_opportunity}."
    )

    return PatentLandscapeReport(
        corpus_name=request.corpus_name,
        patent_count=len(patents),
        assignee_count=len({record.assignee for record in patents}),
        focus_keywords=list(request.focus_keywords),
        summary=summary,
        theme_clusters=theme_clusters,
        whitespace_opportunities=whitespace_opportunities,
        watchlist_patents=watchlist_patents,
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
    )
