from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    DishSplitter,
    InventoryJoiner,
    MenuAdviceSink,
    MenuProfitScorer,
    RestaurantOrderSource,
)


def run_restaurant_sales_analysis_pipeline(input_file: str, output_file: str) -> None:
    env = LocalEnvironment("restaurant_sales_analysis")
    (
        env.from_batch(RestaurantOrderSource, input_file=input_file)
        .flatmap(DishSplitter)
        .map(InventoryJoiner)
        .map(MenuProfitScorer)
        .sink(MenuAdviceSink, output_file=output_file)
    )
    env.submit(autostop=True)
