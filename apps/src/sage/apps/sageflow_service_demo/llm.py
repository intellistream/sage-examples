"""OpenAI-compatible LLM client for the SageFlow service demo."""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .contracts import build_snapshot_prompt, contract_evidence_ids
from .models import LLMGenerationResult, SnapshotContract


@dataclass(frozen=True)
class LLMClientConfig:
    base_url: str
    model: str
    api_key: str = ""
    provider: str = "openai-compatible"
    timeout_seconds: float = 60.0
    temperature: float = 0.2
    max_tokens: int = 512
    extra_request_json: dict[str, Any] | None = None

    @classmethod
    def from_env(cls, prefix: str = "SAGEFLOW_DEMO_LLM") -> "LLMClientConfig | None":
        base_url = os.environ.get(f"{prefix}_BASE_URL") or os.environ.get("VLLM_BASE_URL")
        model = os.environ.get(f"{prefix}_MODEL") or os.environ.get("VLLM_MODEL")
        if not base_url or not model:
            return None
        provider = os.environ.get(f"{prefix}_PROVIDER", "openai-compatible")
        return cls(
            base_url=base_url.rstrip("/"),
            model=model,
            api_key=os.environ.get(f"{prefix}_API_KEY", os.environ.get("OPENAI_API_KEY", "")),
            provider=provider,
            timeout_seconds=float(os.environ.get(f"{prefix}_TIMEOUT_SECONDS", "60")),
            temperature=float(os.environ.get(f"{prefix}_TEMPERATURE", "0.2")),
            max_tokens=int(os.environ.get(f"{prefix}_MAX_TOKENS", "512")),
            extra_request_json=_extra_request_json(prefix, provider),
        )


class OpenAICompatibleChatClient:
    def __init__(self, config: LLMClientConfig) -> None:
        self.config = config

    def generate(self, contract: SnapshotContract) -> LLMGenerationResult:
        prompt = build_snapshot_prompt(contract)
        prompt_hash = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:16]
        evidence_ids = contract_evidence_ids(contract)
        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You produce concise, evidence-grounded incident-response summaries.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if self.config.extra_request_json:
            payload.update(self.config.extra_request_json)
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        started = time.perf_counter()
        request = urllib.request.Request(
            f"{self.config.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read()
            parsed = json.loads(raw.decode("utf-8"))
            answer = _extract_answer(parsed)
            usage = parsed.get("usage", {}) if isinstance(parsed, dict) else {}
            return LLMGenerationResult(
                answer_id=f"answer-{contract.contract_id}",
                contract_id=contract.contract_id,
                model=self.config.model,
                base_url=self.config.base_url,
                status="generated",
                headline=_headline_for_contract(contract),
                answer=answer,
                evidence_ids=evidence_ids,
                prompt_hash=prompt_hash,
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
                prompt_tokens=_int_or_none(usage.get("prompt_tokens")),
                completion_tokens=_int_or_none(usage.get("completion_tokens")),
            )
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            return LLMGenerationResult(
                answer_id=f"answer-{contract.contract_id}",
                contract_id=contract.contract_id,
                model=self.config.model,
                base_url=self.config.base_url,
                status="error",
                headline=_headline_for_contract(contract),
                answer="",
                evidence_ids=evidence_ids,
                prompt_hash=prompt_hash,
                latency_ms=round((time.perf_counter() - started) * 1000, 3),
                error=f"{type(exc).__name__}: {exc}",
            )


class TemplateFallbackLLMClient:
    """Explicit non-paper fallback for local tests and disconnected demos."""

    def __init__(self, *, model: str = "template_fallback", base_url: str = "offline") -> None:
        self.model = model
        self.base_url = base_url

    def generate(self, contract: SnapshotContract) -> LLMGenerationResult:
        prompt = build_snapshot_prompt(contract)
        evidence_ids = contract_evidence_ids(contract)
        cluster = contract.cluster
        answer = (
            f"{cluster.cluster_id} contains {cluster.size} related records. "
            f"Evidence ids: {', '.join(evidence_ids)}. "
            "This is a template fallback and must not be reported as a live vLLM result."
        )
        return LLMGenerationResult(
            answer_id=f"answer-{contract.contract_id}",
            contract_id=contract.contract_id,
            model=self.model,
            base_url=self.base_url,
            status="template_fallback",
            headline=_headline_for_contract(contract),
            answer=answer,
            evidence_ids=evidence_ids,
            prompt_hash=hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:16],
            latency_ms=0.0,
        )


def create_llm_client_from_env() -> OpenAICompatibleChatClient | None:
    config = LLMClientConfig.from_env()
    if config is None:
        return None
    return OpenAICompatibleChatClient(config)


def generate_answer_from_contract(
    contract: SnapshotContract,
    *,
    allow_template_fallback: bool = False,
) -> LLMGenerationResult | None:
    client = create_llm_client_from_env()
    if client is not None:
        return client.generate(contract)
    if allow_template_fallback:
        return TemplateFallbackLLMClient().generate(contract)
    return None


def _extract_answer(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") if isinstance(payload, dict) else None
    if not choices:
        raise RuntimeError("LLM response did not contain choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise RuntimeError("LLM response choice is not an object")
    message = first.get("message")
    if isinstance(message, dict) and message.get("content"):
        return str(message["content"]).strip()
    text = first.get("text")
    if text:
        return str(text).strip()
    raise RuntimeError("LLM response contained no text")


def _headline_for_contract(contract: SnapshotContract) -> str:
    cluster = contract.cluster
    return f"{contract.contract_type}: {cluster.cluster_id} ({cluster.size} records)"


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extra_request_json(prefix: str, provider: str) -> dict[str, Any] | None:
    raw = os.environ.get(f"{prefix}_EXTRA_JSON")
    if raw:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError(f"{prefix}_EXTRA_JSON must decode to a JSON object")
        return parsed
    if provider.lower() in {"zhipu", "bigmodel", "zai", "z.ai"}:
        return {"thinking": {"type": "disabled"}}
    return None
