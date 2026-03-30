"""Literature Report Assistant.

A lightweight assistant that retrieves recent papers, ranks them by topic relevance,
and generates a readable markdown report.
"""

from .pipeline import (
    LiteraturePaper,
    PaperRecommendation,
    ResearchProfile,
    generate_literature_report,
    generate_personalized_recommendation_report,
    preprocess_paper_stream,
    rank_papers,
    recommend_papers,
    search_arxiv_papers,
)

__all__ = [
    "LiteraturePaper",
    "PaperRecommendation",
    "ResearchProfile",
    "generate_literature_report",
    "generate_personalized_recommendation_report",
    "preprocess_paper_stream",
    "rank_papers",
    "recommend_papers",
    "search_arxiv_papers",
]
