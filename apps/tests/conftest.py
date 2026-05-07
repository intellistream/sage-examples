from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _bootstrap_workspace_sage() -> None:
    if importlib.util.find_spec("sage.runtime") is not None:
        return

    sibling_src = Path(__file__).resolve().parents[3] / "SAGE" / "src"
    if sibling_src.is_dir():
        sys.path.insert(0, str(sibling_src))


def _bootstrap_workspace_sageflow() -> None:
    if importlib.util.find_spec("sage_flow") is not None:
        return

    sibling_repo = Path(__file__).resolve().parents[3] / "sageFlow"
    if sibling_repo.is_dir():
        sys.path.insert(0, str(sibling_repo))


_bootstrap_workspace_sage()
_bootstrap_workspace_sageflow()