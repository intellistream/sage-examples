"""Operators for routing service tickets."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sage.apps._batch import ListBatchSource
from sage.foundation import BatchFunction, CustomLogger, FlatMapFunction, MapFunction, SinkFunction


class TicketSource(ListBatchSource):
    def __init__(self, input_file: str, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file

    def load_items(self) -> list[dict[str, Any]]:
        with open(self.input_file, "r", encoding="utf-8", newline="") as handle:
            if self.input_file.lower().endswith(".json"):
                return json.load(handle)
            return list(csv.DictReader(handle))


class TicketParser(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        item["subject"] = str(item.get("subject", "")).strip()
        item["description"] = str(item.get("description", "")).strip()
        item["requester"] = str(item.get("requester", "unknown")).strip()
        return item


class TicketClassifier(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = f"{item.get('subject', '')} {item.get('description', '')}".lower()
        if any(keyword in text for keyword in ["refund", "invoice", "billing", "浠樻"]):
            item["category"] = "billing"
        elif any(keyword in text for keyword in ["bug", "error", "failure", "鏁呴殰"]):
            item["category"] = "technical"
        elif any(keyword in text for keyword in ["complaint", "angry", "鎶曡瘔"]):
            item["category"] = "complaint"
        else:
            item["category"] = "general"
        return item


class PriorityScorer(MapFunction):
    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        text = f"{item.get('subject', '')} {item.get('description', '')}".lower()
        score = 1
        if item.get("category") in {"complaint", "technical"}:
            score += 1
        if any(keyword in text for keyword in ["urgent", "asap", "critical", "涓ラ噸"]):
            score += 2
        item["priority_score"] = score
        item["priority"] = "high" if score >= 4 else "medium" if score >= 2 else "low"
        return item


class LoadBalancer(MapFunction):
    def __init__(self, agents: list[str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.agents = agents or ["agent_a", "agent_b", "agent_c"]
        self.load = {agent: 0 for agent in self.agents}

    def execute(self, item: dict[str, Any]) -> dict[str, Any]:
        assignee = min(self.load, key=self.load.get)
        self.load[assignee] += 1 + int(item.get("priority_score", 1))
        item["assignee"] = assignee
        return item


class NotificationSink(SinkFunction):
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
