"""Embedding cache and OpenAI-compatible embedding client for the demo."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def event_text(payload: dict[str, Any]) -> str:
    parts = [
        str(payload.get("event_id", "")),
        str(payload.get("source", "")),
        str(payload.get("summary", "")),
        " ".join(str(item) for item in payload.get("tags", [])),
    ]
    metadata = payload.get("metadata", {})
    if isinstance(metadata, dict):
        for key in ("title", "vendor", "product", "cwe", "references"):
            value = metadata.get(key)
            if isinstance(value, list):
                parts.append(" ".join(str(item) for item in value))
            elif value is not None:
                parts.append(str(value))
    return "\n".join(part for part in parts if part)


@dataclass(frozen=True)
class EmbeddingClientConfig:
    base_url: str
    model: str
    api_key: str = ""
    timeout_seconds: float = 60.0

    @classmethod
    def from_env(cls, prefix: str = "SAGEFLOW_DEMO_EMBEDDING") -> "EmbeddingClientConfig | None":
        base_url = os.environ.get(f"{prefix}_BASE_URL")
        model = os.environ.get(f"{prefix}_MODEL")
        if not base_url or not model:
            return None
        return cls(
            base_url=base_url.rstrip("/"),
            model=model,
            api_key=os.environ.get(f"{prefix}_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
            timeout_seconds=float(os.environ.get(f"{prefix}_TIMEOUT_SECONDS", "60")),
        )


class OpenAICompatibleEmbeddingClient:
    def __init__(self, config: EmbeddingClientConfig) -> None:
        self.config = config

    def embed(self, text: str) -> list[float]:
        payload = {"model": self.config.model, "input": text}
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        request = urllib.request.Request(
            f"{self.config.base_url}/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"embedding request failed: {exc}") from exc

        data = parsed.get("data") if isinstance(parsed, dict) else None
        if not data or not isinstance(data[0], dict) or "embedding" not in data[0]:
            raise RuntimeError("embedding response did not contain data[0].embedding")
        embedding = data[0]["embedding"]
        if not isinstance(embedding, list) or not embedding:
            raise RuntimeError("embedding response was empty")
        return [float(item) for item in embedding]


class EmbeddingCache:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._by_event_id: dict[str, list[float]] = {}
        self._metadata: dict[str, Any] = {}
        self._load()

    @property
    def metadata(self) -> dict[str, Any]:
        return dict(self._metadata)

    def get(self, event_id: str) -> list[float] | None:
        value = self._by_event_id.get(event_id)
        return list(value) if value is not None else None

    def _load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"embedding cache not found: {self.path}")
        paths = sorted(self.path.glob("*.jsonl")) if self.path.is_dir() else [self.path]
        if not paths:
            raise FileNotFoundError(f"embedding cache directory has no jsonl shards: {self.path}")
        for path in paths:
            self._load_jsonl(path)

    def _load_jsonl(self, path: Path) -> None:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get("type") == "metadata":
                    self._metadata = {**dict(item), "cache_path": str(self.path)}
                    continue
                event_id = str(item.get("event_id", ""))
                embedding = item.get("embedding")
                if not event_id or not isinstance(embedding, list) or not embedding:
                    raise ValueError(f"invalid embedding cache row in {path}")
                self._by_event_id[event_id] = [float(value) for value in embedding]


def load_cache_from_env() -> EmbeddingCache | None:
    path = os.environ.get("SAGEFLOW_DEMO_EMBEDDING_CACHE")
    if not path:
        return None
    return EmbeddingCache(path)


def create_embedding_client_from_env() -> OpenAICompatibleEmbeddingClient | None:
    config = EmbeddingClientConfig.from_env()
    if config is None:
        return None
    return OpenAICompatibleEmbeddingClient(config)
