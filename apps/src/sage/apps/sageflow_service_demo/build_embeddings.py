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
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)

    events = read_jsonl(args.events)
    if args.limit is not None:
        events = events[: args.limit]

    client = OpenAICompatibleEmbeddingClient(
        EmbeddingClientConfig(base_url=args.base_url.rstrip("/"), model=args.model, api_key=args.api_key)
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
                    "base_url": args.base_url.rstrip("/"),
                    "record_count": len(events),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )
        for index, event in enumerate(events, start=1):
            embedding = client.embed(event_text(event))
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


if __name__ == "__main__":
    raise SystemExit(main())
