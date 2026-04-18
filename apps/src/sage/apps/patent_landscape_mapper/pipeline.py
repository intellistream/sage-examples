"""SAGE pipeline entry point for patent landscape mapping."""

from __future__ import annotations

import json
from typing import Any

from sage.foundation import MapFunction, SinkFunction
from sage.runtime import LocalEnvironment

from .analysis import analyze_patent_landscape
from .demo_data import build_demo_focus_keywords, build_demo_patent_corpus
from .models import PatentLandscapeReport, PatentLandscapeRequest, PatentRecord


class ValidatePatentLandscapeRequest(MapFunction):
    def execute(self, data: PatentLandscapeRequest | dict[str, Any]) -> PatentLandscapeRequest:
        request = data if isinstance(data, PatentLandscapeRequest) else PatentLandscapeRequest.from_dict(data)
        if len(request.patents) < 2:
            raise ValueError("Patent landscape mapper requires at least two patents.")
        if request.cluster_count < 2:
            raise ValueError("cluster_count must be at least 2.")
        return request


class AnalyzePatentLandscape(MapFunction):
    def execute(self, data: PatentLandscapeRequest) -> PatentLandscapeReport:
        return analyze_patent_landscape(data)


class ResultCollectorSink(SinkFunction):
    def __init__(self, results: list[PatentLandscapeReport], **kwargs) -> None:
        super().__init__(**kwargs)
        self.results = results

    def execute(self, data: PatentLandscapeReport) -> None:
        self.results.append(data)


def run_patent_landscape_mapper_pipeline(
    patents: list[PatentRecord] | None = None,
    *,
    corpus_name: str = "demo-industrial-ai-patents",
    focus_keywords: list[str] | None = None,
    cluster_count: int = 4,
) -> PatentLandscapeReport:
    request = PatentLandscapeRequest(
        corpus_name=corpus_name,
        patents=patents or build_demo_patent_corpus(),
        focus_keywords=focus_keywords or build_demo_focus_keywords(),
        cluster_count=cluster_count,
    )
    results: list[PatentLandscapeReport] = []

    env = LocalEnvironment("patent_landscape_mapper")
    env.set_console_log_level("ERROR")
    env.from_batch([request]).map(ValidatePatentLandscapeRequest).map(AnalyzePatentLandscape).sink(
        ResultCollectorSink,
        results=results,
    )
    env.submit(autostop=True)
    return results[-1]


def print_patent_landscape_report(
    report: PatentLandscapeReport,
    *,
    top_opportunities: int = 3,
) -> None:
    print("=" * 76)
    print("SAGE Patent Landscape Mapper")
    print("=" * 76)
    print(f"Corpus: {report.corpus_name}")
    print(f"Patents: {report.patent_count}")
    print(f"Assignees: {report.assignee_count}")
    print(f"Focus Keywords: {', '.join(report.focus_keywords)}")
    print()
    print(report.summary)
    print()

    print("Theme Clusters")
    print("-" * 76)
    for cluster in report.theme_clusters:
        assignee_preview = ", ".join(
            f"{name} ({count})" for name, count in list(cluster.assignee_breakdown.items())[:3]
        )
        print(
            f"[{cluster.cluster_id}] {cluster.label} | patents={cluster.patent_count} | "
            f"focus={cluster.average_focus_relevance:.3f} | whitespace={cluster.whitespace_score:.3f}"
        )
        print(f"  top terms: {', '.join(cluster.top_terms)}")
        print(f"  assignees: {assignee_preview}")
        print(f"  representative patents: {', '.join(cluster.representative_patent_ids)}")
        print()

    print("Whitespace Opportunities")
    print("-" * 76)
    for item in report.whitespace_opportunities[:top_opportunities]:
        print(f"- {item.title} | score={item.opportunity_score:.3f}")
        print(f"  keywords: {', '.join(item.target_keywords)}")
        print(f"  support: {', '.join(item.supporting_patent_ids)}")
        print(f"  rationale: {item.rationale}")
        print()

    print("Watchlist")
    print("-" * 76)
    for item in report.watchlist_patents:
        print(
            f"- {item.patent_id} | {item.assignee} | {item.theme_label} | "
            f"watch={item.watch_score:.3f} | focus={item.focus_relevance:.3f}"
        )
        print(f"  {item.title}")
        print(f"  {item.reason}")
        print()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="SAGE Patent Landscape Mapper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m sage.apps.patent_landscape_mapper.pipeline
  python -m sage.apps.patent_landscape_mapper.pipeline --clusters 5
  python -m sage.apps.patent_landscape_mapper.pipeline --focus-keywords "cold chain,biologics logistics"
  python -m sage.apps.patent_landscape_mapper.pipeline --json
        """,
    )
    parser.add_argument(
        "--clusters",
        type=int,
        default=4,
        help="Number of landscape clusters to build (default: 4).",
    )
    parser.add_argument(
        "--focus-keywords",
        type=str,
        default=None,
        help="Comma-separated strategic focus keywords.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the report as JSON instead of a console summary.",
    )
    parser.add_argument(
        "--top-opportunities",
        type=int,
        default=3,
        help="How many whitespace opportunities to display in console mode.",
    )
    args = parser.parse_args()

    focus_keywords = None
    if args.focus_keywords:
        focus_keywords = [item.strip() for item in args.focus_keywords.split(",") if item.strip()]

    report = run_patent_landscape_mapper_pipeline(
        focus_keywords=focus_keywords,
        cluster_count=args.clusters,
    )

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return

    print_patent_landscape_report(report, top_opportunities=args.top_opportunities)


if __name__ == "__main__":
    main()