"""Build a JSONL embedding cache for public demo events."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from .dataset_builder import read_jsonl
from .embeddings import EmbeddingClientConfig, OpenAICompatibleEmbeddingClient, event_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--provider", choices=["openai", "sentence-transformers"], default="openai")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    events = read_jsonl(args.events)
    if args.limit is not None:
        events = events[: args.limit]

    if args.provider == "openai" and not args.base_url:
        raise ValueError("--base-url is required for --provider openai")

    embeddings = (
        _embed_with_openai(events, base_url=args.base_url, model=args.model, api_key=args.api_key)
        if args.provider == "openai"
        else _embed_with_sentence_transformers(events, model=args.model, batch_size=args.batch_size)
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "type": "metadata",
                    "schema": "sageflow_service_demo.embedding_cache.v1",
                    "created_at": dt.datetime.now(dt.UTC).isoformat(),
                    "model": args.model,
                    "provider": args.provider,
                    "base_url": args.base_url.rstrip("/") if args.base_url else "",
                    "record_count": len(events),
                    "embedding_dim": len(embeddings[0]) if embeddings else 0,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )
        for index, (event, embedding) in enumerate(zip(events, embeddings, strict=True), start=1):
            handle.write(
                json.dumps(
                    {
                        "event_id": event["event_id"],
                        "source": event.get("source"),
                        "embedding": embedding,
                        "embedding_dim": len(embedding),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )
            if index % 100 == 0:
                print(f"embedded {index}/{len(events)}")
    print(f"wrote {len(events)} embeddings to {args.out}")
    return 0


def _embed_with_openai(
    events: list[dict],
    *,
    base_url: str,
    model: str,
    api_key: str,
) -> list[list[float]]:
    client = OpenAICompatibleEmbeddingClient(
        EmbeddingClientConfig(base_url=base_url.rstrip("/"), model=model, api_key=api_key)
    )
    return [client.embed(event_text(event)) for event in events]


def _embed_with_sentence_transformers(
    events: list[dict],
    *,
    model: str,
    batch_size: int,
) -> list[list[float]]:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - optional runtime dependency
        raise RuntimeError(
            "sentence-transformers is required for --provider sentence-transformers"
        ) from exc

    encoder = SentenceTransformer(model)
    texts = [event_text(event) for event in events]
    vectors = encoder.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    return [[float(value) for value in vector] for vector in vectors]


if __name__ == "__main__":
    raise SystemExit(main())
