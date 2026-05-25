import os

from sage.apps.sageflow_service_demo.config import (
    apply_runtime_environment,
    experiment_config,
    load_demo_config,
    resolve_config_path,
)
from sage.apps.sageflow_service_demo.run_experiment import _runtime_window_ms_for_config


def test_icpp_demo_config_drives_runtime_environment(monkeypatch) -> None:
    monkeypatch.setenv("ZHIPU_API_KEY", "test-key")
    for key in (
        "SAGEFLOW_DEMO_LLM_BASE_URL",
        "SAGEFLOW_DEMO_LLM_MODEL",
        "SAGEFLOW_DEMO_LLM_PROVIDER",
        "SAGEFLOW_DEMO_LLM_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    config, config_path = load_demo_config("configs/icpp_demo_zhipu.json")

    apply_runtime_environment(config)
    experiment_name, experiment = experiment_config(config, None)

    assert experiment_name == "zhipu_llm"
    assert experiment["generate_llm"] is True
    assert os.environ["SAGEFLOW_DEMO_LLM_BASE_URL"] == "https://open.bigmodel.cn/api/paas/v4"
    assert os.environ["SAGEFLOW_DEMO_LLM_MODEL"] == "glm-4.5"
    assert os.environ["SAGEFLOW_DEMO_LLM_PROVIDER"] == "zhipu"
    assert os.environ["SAGEFLOW_DEMO_LLM_API_KEY"] == "test-key"
    assert resolve_config_path(config["paths"]["events"], config_path).name == "events.jsonl"


def test_runtime_experiment_uses_indexed_sequence_window() -> None:
    config, config_path = load_demo_config("configs/icpp_demo_zhipu.json")
    _, experiment = experiment_config(config, "runtime")

    assert experiment["join_methods"] == ["ivf"]
    assert experiment["measurement_mode"] == "engine"
    assert experiment["runtime_timestamp_mode"] == "sequence"
    assert experiment["parallelism"] == [1, 2, 4]
    assert "nvd_2024_q1_3k" in str(resolve_config_path(experiment["paths"]["events"], config_path))
    assert _runtime_window_ms_for_config(
        runtime_window_ms=None,
        runtime_timestamp_mode=experiment["runtime_timestamp_mode"],
        runtime_event_interval_ms=experiment["runtime_event_interval_ms"],
        window_size=512,
    ) == 5120
