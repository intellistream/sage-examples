"""Structured models for the patent landscape mapper application."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PatentRecord:
    patent_id: str
    title: str
    abstract: str
    assignee: str
    year: int
    jurisdictions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PatentRecord:
        return cls(
            patent_id=str(data["patent_id"]),
            title=str(data["title"]),
            abstract=str(data["abstract"]),
            assignee=str(data["assignee"]),
            year=int(data["year"]),
            jurisdictions=list(data.get("jurisdictions", [])),
            tags=list(data.get("tags", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PatentLandscapeRequest:
    corpus_name: str
    patents: list[PatentRecord]
    focus_keywords: list[str] = field(default_factory=list)
    cluster_count: int = 4
    top_terms_per_cluster: int = 6
    top_patents_per_cluster: int = 3

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PatentLandscapeRequest:
        return cls(
            corpus_name=str(data["corpus_name"]),
            patents=[PatentRecord.from_dict(item) for item in data.get("patents", [])],
            focus_keywords=list(data.get("focus_keywords", [])),
            cluster_count=int(data.get("cluster_count", 4)),
            top_terms_per_cluster=int(data.get("top_terms_per_cluster", 6)),
            top_patents_per_cluster=int(data.get("top_patents_per_cluster", 3)),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["patents"] = [item.to_dict() for item in self.patents]
        return payload


@dataclass(frozen=True)
class ThemeCluster:
    cluster_id: int
    label: str
    top_terms: list[str]
    patent_ids: list[str]
    patent_count: int
    representative_patent_ids: list[str]
    assignee_breakdown: dict[str, int]
    average_focus_relevance: float
    whitespace_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WhiteSpaceOpportunity:
    cluster_id: int
    title: str
    rationale: str
    target_keywords: list[str]
    opportunity_score: float
    supporting_patent_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PatentWatchItem:
    patent_id: str
    title: str
    assignee: str
    theme_label: str
    watch_score: float
    focus_relevance: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LandscapeGraphNode:
    node_id: str
    node_type: str
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LandscapeGraphEdge:
    source_id: str
    target_id: str
    relation: str
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PatentLandscapeReport:
    corpus_name: str
    patent_count: int
    assignee_count: int
    focus_keywords: list[str]
    summary: str
    theme_clusters: list[ThemeCluster]
    whitespace_opportunities: list[WhiteSpaceOpportunity]
    watchlist_patents: list[PatentWatchItem]
    graph_nodes: list[LandscapeGraphNode]
    graph_edges: list[LandscapeGraphEdge]

    def to_dict(self) -> dict[str, Any]:
        return {
            "corpus_name": self.corpus_name,
            "patent_count": self.patent_count,
            "assignee_count": self.assignee_count,
            "focus_keywords": list(self.focus_keywords),
            "summary": self.summary,
            "theme_clusters": [item.to_dict() for item in self.theme_clusters],
            "whitespace_opportunities": [item.to_dict() for item in self.whitespace_opportunities],
            "watchlist_patents": [item.to_dict() for item in self.watchlist_patents],
            "graph_nodes": [item.to_dict() for item in self.graph_nodes],
            "graph_edges": [item.to_dict() for item in self.graph_edges],
        }