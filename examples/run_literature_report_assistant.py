#!/usr/bin/env python3
"""Run a lightweight literature report assistant demo."""

from __future__ import annotations

from sage.apps.literature_report_assistant import (
    generate_literature_report,
    rank_papers,
    search_arxiv_papers,
)


def main() -> None:
    topic = "RAG agentic retrieval"
    print(f"🔎 检索主题: {topic}")

    papers = search_arxiv_papers(topic, max_results=12)
    ranked = rank_papers(papers, topic=topic, top_k=5)
    report = generate_literature_report(topic, ranked)

    print("\n" + "=" * 80)
    print(report)
    print("=" * 80)


if __name__ == "__main__":
    main()
