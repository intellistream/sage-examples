"""Side-by-side runtime API layering demo.

This example compares three entry styles with one shared workload shape:

1) Facade API (`create/submit/run/call`) as default tier
2) LocalEnvironment as advanced tier
3) FlownetEnvironment as advanced tier

The demo is contract-oriented and uses controlled mocks for runtime wiring,
so it can run quickly in local development while preserving semantic parity.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any
from unittest.mock import MagicMock, patch

from sage.kernel.api import FlownetEnvironment, LocalEnvironment
from sage.kernel.facade import call, submit


@dataclass
class ApiRunReport:
    api: str
    result: list[int]
    submit_ref_type: str
    error_propagates: bool


def _workload(values: list[int]) -> list[int]:
    return [value * 2 for value in values]


def run_with_facade(payload: list[int]) -> ApiRunReport:
    run_handle = MagicMock(name="facade_run_handle")
    run_handle.call.return_value = _workload(payload)

    backend = MagicMock(name="facade_backend")
    backend.submit.return_value = run_handle

    with patch("sage.kernel.facade._get_runtime_backend", return_value=backend):
        with patch("sage.kernel.facade._resolve_flow_for_backend", lambda obj: obj):
            ref = submit("demo-flow")
            result = call(ref, payload)

    with patch("sage.kernel.facade._get_runtime_backend", return_value=backend):
        with patch("sage.kernel.facade._resolve_flow_for_backend", lambda obj: obj):
            backend.submit.side_effect = RuntimeError("facade-error")
            error_propagates = False
            try:
                submit("demo-flow")
            except RuntimeError as exc:
                error_propagates = str(exc) == "facade-error"

    return ApiRunReport(
        api="facade",
        result=result,
        submit_ref_type=type(ref).__name__,
        error_propagates=error_propagates,
    )


def run_with_local_environment(payload: list[int]) -> ApiRunReport:
    env = LocalEnvironment("examples_local_runtime_api")
    env._jobmanager = MagicMock(name="local_jobmanager")
    env._jobmanager.submit_job.return_value = "local-job-1"
    ref = env.submit(autostop=False)
    result = _workload(payload)

    env._jobmanager.submit_job.side_effect = RuntimeError("local-error")
    error_propagates = False
    try:
        env.submit(autostop=False)
    except RuntimeError as exc:
        error_propagates = str(exc) == "local-error"

    return ApiRunReport(
        api="local_environment",
        result=result,
        submit_ref_type=type(ref).__name__,
        error_propagates=error_propagates,
    )


def run_with_flownet_environment(payload: list[int]) -> ApiRunReport:
    env = FlownetEnvironment("examples_flownet_runtime_api")

    stream_handle = MagicMock(name="stream_handle")
    stream_handle.is_running = True
    compiled_graph = MagicMock(name="compiled_graph")
    compiled_graph.submit.return_value = stream_handle

    compiler_instance = MagicMock(name="pipeline_compiler")
    compiler_instance.compile.return_value = compiled_graph

    with patch("sage.platform.runtime.adapters.flownet_adapter.get_flownet_adapter", return_value=MagicMock()):
        with patch("sage.kernel.flow.pipeline_compiler.PipelineCompiler", return_value=compiler_instance):
            ref = env.submit(autostop=False)
            result = _workload(payload)

    with patch("sage.platform.runtime.adapters.flownet_adapter.get_flownet_adapter", return_value=MagicMock()):
        with patch("sage.kernel.flow.pipeline_compiler.PipelineCompiler", return_value=compiler_instance):
            compiled_graph.submit.side_effect = RuntimeError("flownet-error")
            error_propagates = False
            try:
                env.submit(autostop=False)
            except RuntimeError as exc:
                error_propagates = str(exc) == "flownet-error"

    return ApiRunReport(
        api="flownet_environment",
        result=result,
        submit_ref_type=type(ref).__name__,
        error_propagates=error_propagates,
    )


def _select_reports(mode: str, payload: list[int]) -> list[ApiRunReport]:
    if mode == "facade":
        return [run_with_facade(payload)]
    if mode == "local":
        return [run_with_local_environment(payload)]
    if mode == "flownet":
        return [run_with_flownet_environment(payload)]
    return [
        run_with_facade(payload),
        run_with_local_environment(payload),
        run_with_flownet_environment(payload),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="SAGE runtime API layering demo")
    parser.add_argument(
        "--mode",
        choices=["all", "facade", "local", "flownet"],
        default="all",
        help="Which API tier demo to run",
    )
    parser.add_argument(
        "--payload",
        nargs="*",
        type=int,
        default=[1, 2, 3],
        help="Input integers for shared workload",
    )
    args = parser.parse_args()

    reports = _select_reports(args.mode, args.payload)
    result_doc: dict[str, Any] = {
        "payload": args.payload,
        "reports": [asdict(report) for report in reports],
    }
    print(json.dumps(result_doc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
