#!/usr/bin/env python3
"""Run a lightweight literature report assistant demo."""

from __future__ import annotations

from sage.apps.literature_report_assistant import (
    ResearchProfile,
    generate_personalized_recommendation_report,
    preprocess_paper_stream,
    recommend_papers,
    search_arxiv_papers,
)


def main() -> None:
    topic = "RAG agentic retrieval"
    profile = ResearchProfile(
        interests=["科研推荐", "流式文献处理"],
        keywords=["rag", "retrieval", "agentic", "stream"],
    )
    print(f"🔎 检索主题: {topic}")

    papers = search_arxiv_papers(topic, max_results=12)
    cleaned = preprocess_paper_stream(papers)
    recommendations = recommend_papers(cleaned, profile=profile, top_k=5)
    report = generate_personalized_recommendation_report(topic, recommendations)

    print("\n" + "=" * 80)
    print(report)
    print("=" * 80)


if __name__ == "__main__":
    main()
