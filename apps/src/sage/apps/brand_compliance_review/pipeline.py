from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import BrandReviewSink, BrandAssetSource, BrandAssetParser, BrandRuleMatcher, BrandRiskScorer


def run_brand_compliance_review_pipeline(asset_dir: str, output_file: str) -> None:
    env = LocalEnvironment('brand_compliance_review')
    (
        env.from_batch(BrandAssetSource, asset_dir=asset_dir)
        .map(BrandAssetParser)
        .map(BrandRuleMatcher)
        .map(BrandRiskScorer)
        .sink(BrandReviewSink, output_file=output_file)
    )
    env.submit(autostop=True)
