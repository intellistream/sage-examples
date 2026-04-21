"""
Web Scraper Pipeline
"""

from __future__ import annotations

from sage.foundation import CustomLogger
from sage.runtime import LocalEnvironment

from .operators import DatabaseSink, TableExtractor, UrlSource, WebScraper


def run_web_scraper_pipeline(url_file: str, output_file: str, verbose: bool = False) -> None:
    logger = CustomLogger("WebScraperPipeline")
    if verbose:
        logger.info(f"Starting web scraper: {url_file} -> {output_file}")

    env = LocalEnvironment("web_scraper")
    (
        env.from_batch(UrlSource, url_file=url_file)
        .map(WebScraper)
        .flatmap(TableExtractor)
        .sink(DatabaseSink, output_file=output_file)
    )
    env.submit(autostop=True)

    if verbose:
        logger.info("Web scraper pipeline finished")
