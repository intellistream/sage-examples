"""Shared test fixtures for locally developed generated apps."""

from __future__ import annotations

import logging
import sys
import types
from pathlib import Path


def pytest_configure() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    apps_src = repo_root / "src"
    sage_root = apps_src / "sage"
    apps_root = sage_root / "apps"

    for key in list(sys.modules):
        if key == "sage" or key.startswith("sage."):
            del sys.modules[key]

    sage_pkg = types.ModuleType("sage")
    sage_pkg.__path__ = [str(sage_root)]
    sys.modules["sage"] = sage_pkg

    foundation = types.ModuleType("sage.foundation")

    class _Base:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class BatchFunction(_Base):
        pass

    class MapFunction(_Base):
        pass

    class FlatMapFunction(_Base):
        pass

    class SinkFunction(_Base):
        pass

    class CustomLogger:
        def __init__(self, name: str):
            self._logger = logging.getLogger(name)

        def info(self, message: str) -> None:
            self._logger.info(message)

        def error(self, message: str) -> None:
            self._logger.error(message)

    foundation.BatchFunction = BatchFunction
    foundation.MapFunction = MapFunction
    foundation.FlatMapFunction = FlatMapFunction
    foundation.SinkFunction = SinkFunction
    foundation.CustomLogger = CustomLogger
    sys.modules["sage.foundation"] = foundation

    runtime = types.ModuleType("sage.runtime")

    class _Pipeline:
        def map(self, *args, **kwargs):
            return self

        def flat_map(self, *args, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def sink(self, *args, **kwargs):
            return self

    class LocalEnvironment:
        def __init__(self, name: str):
            self.name = name

        def from_batch(self, *args, **kwargs):
            return _Pipeline()

        def submit(self, autostop: bool = True):
            return None

    runtime.LocalEnvironment = LocalEnvironment
    sys.modules["sage.runtime"] = runtime

    apps_pkg = types.ModuleType("sage.apps")
    apps_pkg.__path__ = [str(apps_root)]
    version_ns: dict[str, object] = {}
    exec((apps_root / "_version.py").read_text(encoding="utf-8"), version_ns)
    apps_pkg.__version__ = version_ns["__version__"]
    sys.modules["sage.apps"] = apps_pkg
    sage_pkg.apps = apps_pkg
