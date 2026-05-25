"""Machine-readable configuration helpers for the ICPP demo pipeline."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, MutableMapping


def load_demo_config(path: str | Path | None) -> tuple[dict[str, Any], Path | None]:
    if path is None:
        return {}, None
    config_path = Path(path).expanduser().resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"demo config must be a JSON object: {config_path}")
    return payload, config_path


def resolve_config_path(value: str | Path | None, config_path: Path | None) -> Path | None:
    if value is None:
        return None
    path = Path(value).expanduser()
    if path.is_absolute() or config_path is None:
        return path.resolve()
    return (config_path.parent / path).resolve()


def apply_runtime_environment(
    config: dict[str, Any],
    *,
    env: MutableMapping[str, str] | None = None,
    override: bool = False,
) -> None:
    env = env if env is not None else os.environ
    llm = config.get("llm")
    if isinstance(llm, dict):
        _set_env(env, "SAGEFLOW_DEMO_LLM_BASE_URL", llm.get("base_url"), override=override)
        _set_env(env, "SAGEFLOW_DEMO_LLM_MODEL", llm.get("model"), override=override)
        _set_env(env, "SAGEFLOW_DEMO_LLM_PROVIDER", llm.get("provider"), override=override)
        _set_env(env, "SAGEFLOW_DEMO_LLM_TEMPERATURE", llm.get("temperature"), override=override)
        _set_env(env, "SAGEFLOW_DEMO_LLM_MAX_TOKENS", llm.get("max_tokens"), override=override)
        _set_env(env, "SAGEFLOW_DEMO_LLM_TIMEOUT_SECONDS", llm.get("timeout_seconds"), override=override)
        if isinstance(llm.get("extra_json"), dict):
            _set_env(
                env,
                "SAGEFLOW_DEMO_LLM_EXTRA_JSON",
                json.dumps(llm["extra_json"], ensure_ascii=False, sort_keys=True),
                override=override,
            )
        api_key_env = llm.get("api_key_env")
        if isinstance(api_key_env, str) and env.get(api_key_env):
            _set_env(env, "SAGEFLOW_DEMO_LLM_API_KEY", env[api_key_env], override=override)


def experiment_config(config: dict[str, Any], name: str | None) -> tuple[str | None, dict[str, Any]]:
    experiments = config.get("experiments")
    if not isinstance(experiments, dict) or not experiments:
        return None, {}
    experiment_name = name or str(config.get("default_experiment") or next(iter(experiments)))
    selected = experiments.get(experiment_name)
    if not isinstance(selected, dict):
        raise ValueError(f"unknown demo experiment config: {experiment_name}")
    return experiment_name, selected


def _set_env(
    env: MutableMapping[str, str],
    key: str,
    value: object,
    *,
    override: bool,
) -> None:
    if value is None or value == "":
        return
    if not override and env.get(key):
        return
    env[key] = str(value)
