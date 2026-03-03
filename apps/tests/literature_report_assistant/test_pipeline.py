from sage.apps.literature_report_assistant.pipeline import (
    LiteraturePaper,
    ResearchProfile,
    generate_literature_report,
    generate_personalized_recommendation_report,
    preprocess_paper_stream,
    rank_papers,
    recommend_papers,
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


def test_preprocess_stream_deduplicates_and_normalizes() -> None:
    papers = [
        LiteraturePaper(
            title="  Agentic   RAG  ",
            summary="  First   summary.  ",
            url="https://arxiv.org/abs/1111.1111 ",
            published="2026-01-01",
        ),
        LiteraturePaper(
            title="Agentic RAG",
            summary="First summary.",
            url="https://arxiv.org/abs/1111.1111",
            published="2026-01-01",
        ),
    ]

    cleaned = preprocess_paper_stream(papers)
    assert len(cleaned) == 1
    assert cleaned[0].title == "Agentic RAG"
    assert cleaned[0].summary == "First summary."


def test_recommend_papers_returns_reasoned_results() -> None:
    papers = [
        LiteraturePaper(
            title="Streaming RAG for Scientific Recommendation",
            summary="Real-time retrieval and recommendation for arXiv streams.",
            url="https://arxiv.org/abs/2222.2222",
            published="2026-02-10",
        ),
        LiteraturePaper(
            title="Classic computer vision benchmark",
            summary="No relevance to LLM literature recommendation.",
            url="https://arxiv.org/abs/3333.3333",
            published="2026-02-11",
        ),
    ]
    profile = ResearchProfile(interests=["scientific recommendation"], keywords=["rag", "stream"])

    recommendations = recommend_papers(papers, profile, top_k=3)
    assert len(recommendations) == 1
    assert "匹配关键词" in recommendations[0].reason
    assert "RAG" in recommendations[0].paper.title


def test_personalized_report_contains_reason() -> None:
    profile = ResearchProfile(interests=["agentic"], keywords=["rag"])
    recommendations = recommend_papers(
        [
            LiteraturePaper(
                title="Agentic RAG Survey",
                summary="Survey on agentic retrieval systems.",
                url="https://arxiv.org/abs/4444.4444",
                published="2026-03-01",
            )
        ],
        profile,
        top_k=1,
    )

    report = generate_personalized_recommendation_report("agentic rag", recommendations)
    assert "个性化文献推荐报告" in report
    assert "推荐理由" in report
    assert "Agentic RAG Survey" in report
