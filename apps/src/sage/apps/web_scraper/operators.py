"""
Web Scraper Operators

Lightweight operators for web scraping and table extraction.
"""

from __future__ import annotations

import json
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import CustomLogger, FlatMapFunction, MapFunction, SinkFunction


class UrlSource(ListBatchSource):
    def __init__(self, url_file: str, **kwargs):
        super().__init__(**kwargs)
        self.url_file = url_file
        self._source_logger = CustomLogger("UrlSource")

    def load_items(self) -> list[str]:
        urls = []
        try:
            with open(self.url_file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        urls.append(line.strip())
            self.logger.info(f"Read {len(urls)} URLs from {self.url_file}")
        except Exception as e:
            self.logger.error(f"Error reading URL file: {e}")
        return urls


class WebScraper(MapFunction):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._scraper_logger = CustomLogger("WebScraper")

    def execute(self, data: str) -> dict[str, Any]:
        import requests
        from bs4 import BeautifulSoup

        try:
            resp = requests.get(data, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            title = soup.title.string if soup.title else ""
            return {"url": data, "title": title, "html": resp.text}
        except Exception as e:
            self.logger.error(f"Failed to fetch {data}: {e}")
            return {"url": data, "title": "", "html": ""}


class TableExtractor(FlatMapFunction):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._extractor_logger = CustomLogger("TableExtractor")

    def execute(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        from bs4 import BeautifulSoup

        html = data.get("html", "")
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        tables = []
        for table in soup.find_all("table"):
            rows = []
            for tr in table.find_all("tr"):
                cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cols:
                    rows.append(cols)
            if rows:
                tables.append({"url": data.get("url"), "rows": rows})
        return tables


class DatabaseSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self._sink_logger = CustomLogger("DatabaseSink")
        self.count = 0

    def setup(self, context: Any) -> None:
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("[\n")

    def execute(self, data: dict[str, Any]) -> None:
        with open(self.output_file, "a", encoding="utf-8") as f:
            if self.count > 0:
                f.write(",\n")
            json.dump(data, f, ensure_ascii=False)
            self.count += 1

    def teardown(self, context: Any) -> None:
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write("\n]")
        self.logger.info(f"Written {self.count} tables to {self.output_file}")
