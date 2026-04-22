from __future__ import annotations

from sage.runtime import LocalEnvironment

from .operators import (
    InvoiceMatcher,
    InvoiceSource,
    OrderSource,
    ReconciliationFieldNormalizer,
    ReconciliationSink,
)


def run_invoice_reconciliation_pipeline(
    input_file: str, output_file: str, order_file: str | None = None, tolerance: float = 1.0
) -> None:
    env = LocalEnvironment("invoice_reconciliation")
    (
        env.from_batch(InvoiceSource, input_file=input_file)
        .map(OrderSource, order_file=order_file)
        .map(ReconciliationFieldNormalizer)
        .map(InvoiceMatcher, tolerance=tolerance)
        .sink(ReconciliationSink, output_file=output_file)
    )
    env.submit(autostop=True)
