from sage.apps.literature_report_assistant.pipeline import (
    LiteraturePaper,
    generate_literature_report,
    rank_papers,
)


def test_rank_papers_prefers_topic_overlap() -> None:
    papers = [
        LiteraturePaper(
            title="Agentic RAG with tool use",
            summary="A retrieval augmented generation framework for agent systems.",
            url="https://arxiv.org/abs/0001.00001",
            published="2026-01-01",
        ),
        LiteraturePaper(
            title="Image denoising baseline",
            summary="Classical denoising for grayscale images.",
            url="https://arxiv.org/abs/0001.00002",
            published="2026-01-02",
        ),
    ]

    ranked = rank_papers(papers, topic="agentic rag retrieval", top_k=1)
    assert len(ranked) == 1
    assert "RAG" in ranked[0].title


def test_generate_report_contains_topic_and_papers() -> None:
    papers = [
        LiteraturePaper(
            title="RAG Survey",
            summary="Comprehensive survey on retrieval-augmented generation.",
            url="https://arxiv.org/abs/1234.5678",
            published="2026-02-01",
        )
    ]
    report = generate_literature_report("RAG", papers)
    assert "文献阅读报告：RAG" in report
    assert "RAG Survey" in report
    assert "建议阅读顺序" in report
