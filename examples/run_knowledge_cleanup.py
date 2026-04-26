#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.knowledge_cleanup import run_knowledge_cleanup_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.knowledge_cleanup: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run knowledge cleanup")
    parser.add_argument("--article-dir", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()
    run_knowledge_cleanup_pipeline(args.article_dir, args.output_file)


if __name__ == "__main__":
    main()
