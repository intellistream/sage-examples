from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import MapFunction, SinkFunction


def _load_records(input_file: str) -> list[dict[str, Any]]:
    with open(input_file, encoding="utf-8", newline="") as handle:
        if input_file.lower().endswith(".json"):
            return json.load(handle)
        return list(csv.DictReader(handle))


class ContentPublishSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        return _load_records(self.input_file)


class SubscriptionMatcher(MapFunction):
    def __init__(self, subscription_file: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.subscription_file = subscription_file
        self._subscriptions = _load_records(subscription_file) if subscription_file else []

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        topic = str(item.get("topic") or item.get("category") or "general").lower()
        matches = []
        for subscription in self._subscriptions:
            subscribed_topic = str(
                subscription.get("topic") or subscription.get("interest") or ""
            ).lower()
            if topic and topic in subscribed_topic or subscribed_topic in topic:
                matches.append(subscription)
        item["matched_subscriptions"] = matches
        return item


class PersonalizationFilter(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        headline = str(item.get("title") or item.get("headline") or "")
        personalized = []
        for subscription in item.get("matched_subscriptions", []):
            personalized.append(
                {
                    "subscriber_id": subscription.get("subscriber_id")
                    or subscription.get("user_id")
                    or "unknown",
                    "channel": subscription.get("channel") or "email",
                    "message": f"{headline} | match_topic={subscription.get('topic') or subscription.get('interest')}",
                }
            )
        item["dispatch_targets"] = personalized
        return item


class DispatchSink(SinkFunction):
    def __init__(self, output_file: str, **kwargs):
        super().__init__(**kwargs)
        self.output_file = output_file
        self.items: list[dict[str, Any]] = []

    def execute(self, item: dict[str, Any]) -> None:
        self.items.append(item)

    def teardown(self, context: Any) -> None:
        Path(self.output_file).write_text(
            json.dumps(self.items, ensure_ascii=False, indent=2), encoding="utf-8"
        )
