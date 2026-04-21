#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

try:
    from sage.apps.mail_classifier import run_mail_classifier_pipeline
except ImportError as exc:
    print(f"Error importing sage.apps.mail_classifier: {exc}")
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run mail classifier pipeline")
    parser.add_argument("--input-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run_mail_classifier_pipeline(args.input_file, args.output)


if __name__ == "__main__":
    main()
