"""Operator collection for the video intelligence demo."""

from __future__ import annotations

from importlib import import_module

_SYMBOL_TO_MODULE = {
    "VideoFrameSource": ".sources",
    "FramePreprocessor": ".preprocessing",
    "SceneConceptExtractor": ".perception",
    "FrameObjectClassifier": ".perception",
    "TemporalAnomalyDetector": ".analytics",
    "FrameEventEmitter": ".analytics",
    "SlidingWindowSummaryEmitter": ".analytics",
    "FrameLightweightFormatter": ".formatters",
    "SageMiddlewareIntegrator": ".integrations",
    "SummaryMemoryAugmentor": ".integrations",
    "TimelineSink": ".sinks",
    "SummarySink": ".sinks",
    "EventStatsSink": ".sinks",
}


def __getattr__(name: str):
    module_name = _SYMBOL_TO_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value

__all__ = [
    "VideoFrameSource",
    "FramePreprocessor",
    "SceneConceptExtractor",
    "FrameObjectClassifier",
    "TemporalAnomalyDetector",
    "FrameEventEmitter",
    "SlidingWindowSummaryEmitter",
    "FrameLightweightFormatter",
    "SageMiddlewareIntegrator",
    "SummaryMemoryAugmentor",
    "TimelineSink",
    "SummarySink",
    "EventStatsSink",
]
