from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    MediaArchiveSink,
    MediaAssetSource,
    MediaDuplicateDetector,
    MediaMetadataExtractor,
    MediaTagger,
)


def run_media_archive_search_pipeline(asset_dir: str, output_dir: str) -> None:
    env = LocalEnvironment("media_archive_search")
    (
        env.from_batch(MediaAssetSource, asset_dir=asset_dir)
        .map(MediaMetadataExtractor)
        .map(MediaTagger)
        .map(MediaDuplicateDetector)
        .sink(MediaArchiveSink, output_dir=output_dir)
    )
    env.submit(autostop=True)
