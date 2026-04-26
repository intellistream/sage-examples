"""Inventory alert pipeline."""

from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    AlertLevelMapper,
    AlertSink,
    InventoryAnomalyScorer,
    InventoryFeatureBuilder,
    InventorySource,
)


def run_inventory_alert_pipeline(
    input_file: str, output_file: str, config_path: str | None = None
) -> None:
    env = LocalEnvironment("inventory_alert")
    (
        env.from_batch(InventorySource, input_file=input_file)
        .map(InventoryFeatureBuilder)
        .map(InventoryAnomalyScorer)
        .map(AlertLevelMapper)
        .sink(AlertSink, output_file=output_file)
    )
    env.submit(autostop=True)
