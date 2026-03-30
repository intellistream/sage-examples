"""Pipeline for literature search and report generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

ARXIV_API = "http://export.arxiv.org/api/query"


@dataclass(frozen=True)
class LiteraturePaper:
    """Single paper item used by the report assistant."""

    title: str
    summary: str
    url: str
    published: str


@dataclass(frozen=True)
class ResearchProfile:
    """User profile for personalized paper recommendation."""

    interests: list[str]
    keywords: list[str]


@dataclass(frozen=True)
class PaperRecommendation:
    """A scored recommendation item with explanation."""

    paper: LiteraturePaper
    score: float
    reason: str


def search_arxiv_papers(
    topic: str, max_results: int = 10, timeout: int = 20
) -> list[LiteraturePaper]:
    """Search arXiv papers by topic.

    Falls back to an empty list on transient HTTP/XML parsing errors to keep this
    assistant usable in offline/example environments.
    """
    query = quote_plus(topic.strip())
    request_url = (
        f"{ARXIV_API}?search_query=all:{query}&start=0&max_results={max_results}"
        "&sortBy=submittedDate&sortOrder=descending"
    )

    try:
        response = requests.get(request_url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, "xml")
    entries = soup.find_all("entry")

    papers: list[LiteraturePaper] = []
    for entry in entries:
        title = (entry.find("title").text or "").strip() if entry.find("title") else ""
        summary = (entry.find("summary").text or "").strip() if entry.find("summary") else ""
        link = entry.find("id")
        published = entry.find("published")
        papers.append(
            LiteraturePaper(
                title=title,
                summary=summary,
                url=(link.text.strip() if link else ""),
                published=(published.text.strip() if published else ""),
            )
        )

    return papers


def rank_papers(
    papers: Iterable[LiteraturePaper], topic: str, top_k: int = 5
) -> list[LiteraturePaper]:
    """Rank papers with a simple keyword overlap score."""
    topic_tokens = {token.lower() for token in topic.split() if token.strip()}
    if not topic_tokens:
        return list(papers)[:top_k]

    scored: list[tuple[float, LiteraturePaper]] = []
    for paper in papers:
        text = f"{paper.title} {paper.summary}".lower()
        overlap = sum(1 for token in topic_tokens if token in text)
        length_penalty = max(len(paper.summary), 1)
        score = overlap + min(0.2, 200.0 / length_penalty)
        scored.append((score, paper))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [paper for _, paper in scored[:top_k]]


def preprocess_paper_stream(papers: Iterable[LiteraturePaper]) -> list[LiteraturePaper]:
    """Normalize and deduplicate paper stream records."""
    normalized: list[LiteraturePaper] = []
    seen_keys: set[str] = set()

    for paper in papers:
        title = " ".join(paper.title.split())
        summary = " ".join(paper.summary.split())
        url = paper.url.strip()
        key = (url or title).lower()
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        normalized.append(
            LiteraturePaper(
                title=title,
                summary=summary,
                url=url,
                published=paper.published.strip(),
            )
        )

    return normalized


def recommend_papers(
    papers: Iterable[LiteraturePaper],
    profile: ResearchProfile,
    top_k: int = 5,
) -> list[PaperRecommendation]:
    """Generate personalized paper recommendations with reasons."""
    profile_tokens = {
        token.lower()
        for token in [*profile.interests, *profile.keywords]
        if isinstance(token, str) and token.strip()
    }

    if not profile_tokens:
        return [
            PaperRecommendation(paper=paper, score=0.0, reason="未提供画像关键词，按原始顺序返回")
            for paper in list(papers)[:top_k]
        ]

    recommendations: list[PaperRecommendation] = []
    for paper in papers:
        text = f"{paper.title} {paper.summary}".lower()
        matched_tokens = [token for token in sorted(profile_tokens) if token in text]
        if not matched_tokens:
            continue

        coverage = len(matched_tokens)
        freshness_bonus = 0.1 if paper.published else 0.0
        score = float(coverage) + freshness_bonus
        reason = f"匹配关键词: {', '.join(matched_tokens[:4])}"
        recommendations.append(PaperRecommendation(paper=paper, score=score, reason=reason))

    recommendations.sort(key=lambda item: item.score, reverse=True)
    return recommendations[:top_k]


def generate_literature_report(topic: str, papers: list[LiteraturePaper]) -> str:
    """Generate a markdown literature reading report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# 文献阅读报告：{topic}",
        "",
        f"生成时间：{now}",
        f"候选文献数：{len(papers)}",
        "",
        "## 核心发现",
    ]

    if not papers:
        lines.extend(
            [
                "- 本次未检索到可用文献（可能是网络受限或主题过窄）。",
                "- 建议扩展关键词或稍后重试。",
                "",
            ]
        )
        return "\n".join(lines)

    for index, paper in enumerate(papers, start=1):
        brief = paper.summary.replace("\n", " ").strip()
        if len(brief) > 260:
            brief = f"{brief[:257]}..."
        lines.extend(
            [
                f"### {index}. {paper.title}",
                f"- 发表时间：{paper.published or '未知'}",
                f"- 链接：{paper.url or 'N/A'}",
                f"- 摘要：{brief}",
                "",
            ]
        )

    lines.extend(
        [
            "## 建议阅读顺序",
            "- 先阅读排名靠前的 1-2 篇，把握最新方向。",
            "- 再按方法或数据集相似度挑选后续文献深入。",
        ]
    )

    return "\n".join(lines)


def generate_personalized_recommendation_report(
    topic: str,
    recommendations: list[PaperRecommendation],
) -> str:
    """Generate markdown report for personalized recommendations."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# 个性化文献推荐报告：{topic}",
        "",
        f"生成时间：{now}",
        f"推荐条目数：{len(recommendations)}",
        "",
        "## 推荐结果",
    ]

    if not recommendations:
        lines.append("- 未找到与当前画像匹配的文献，建议扩大兴趣关键词范围。")
        return "\n".join(lines)

    for index, item in enumerate(recommendations, start=1):
        lines.extend(
            [
                f"### {index}. {item.paper.title}",
                f"- 分数：{item.score:.2f}",
                f"- 推荐理由：{item.reason}",
                f"- 发表时间：{item.paper.published or '未知'}",
                f"- 链接：{item.paper.url or 'N/A'}",
                "",
            ]
        )

    return "\n".join(lines)
