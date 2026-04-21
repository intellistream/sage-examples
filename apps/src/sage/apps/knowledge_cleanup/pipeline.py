from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import KnowledgeCleanupSink, KnowledgeArticleSource, KnowledgeFingerprintBuilder, KnowledgeDuplicateDetector, KnowledgeFreshnessScorer


def run_knowledge_cleanup_pipeline(article_dir: str, output_file: str) -> None:
    env = LocalEnvironment('knowledge_cleanup')
    (
        env.from_batch(KnowledgeArticleSource, article_dir=article_dir)
        .map(KnowledgeFingerprintBuilder)
        .map(KnowledgeDuplicateDetector)
        .map(KnowledgeFreshnessScorer)
        .sink(KnowledgeCleanupSink, output_file=output_file)
    )
    env.submit(autostop=True)
