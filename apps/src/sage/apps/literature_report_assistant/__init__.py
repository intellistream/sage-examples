"""Literature Report Assistant.

A lightweight assistant that retrieves recent papers, ranks them by topic relevance,
and generates a readable markdown report.
"""

from .pipeline import (
    LiteraturePaper,
    generate_literature_report,
    rank_papers,
    search_arxiv_papers,
)

__all__ = [
    "LiteraturePaper",
    "generate_literature_report",
    "rank_papers",
    "search_arxiv_papers",
]
