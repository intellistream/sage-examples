"""Optional OpenAI-compatible LLM integration for the student improvement app."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import httpx
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependency availability is environment-specific
    httpx = None
    OpenAI = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency availability is environment-specific
    load_dotenv = None


DEFAULT_BASE_URL = "https://api.sage.org.ai/v1"
DEFAULT_USER_AGENT = "python-httpx/0.28.1"


def _load_local_env_file(env_file: str | os.PathLike[str] | None = None) -> None:
    if load_dotenv is None:
        return

    candidate_paths: list[Path] = []
    if env_file is not None:
        candidate_paths.append(Path(env_file).expanduser())
    else:
        candidate_paths.append(Path.cwd() / ".env")
        for parent in Path(__file__).resolve().parents:
            candidate_paths.append(parent / ".env")

    seen_paths: set[Path] = set()
    for candidate_path in candidate_paths:
        resolved_path = candidate_path.resolve()
        if resolved_path in seen_paths:
            continue
        seen_paths.add(resolved_path)
        if resolved_path.is_file():
            load_dotenv(dotenv_path=resolved_path, override=False)
            return


@dataclass(frozen=True)
class SageOpenAISettings:
    base_url: str
    api_key: str | None
    model: str | None = None

    @classmethod
    def from_env(cls, env_file: str | os.PathLike[str] | None = None) -> SageOpenAISettings:
        _load_local_env_file(env_file)
        return cls(
            base_url=os.getenv("SAGE_OPENAI_BASE_URL", DEFAULT_BASE_URL),
            api_key=os.getenv("SAGE_OPENAI_API_KEY"),
            model=os.getenv("SAGE_OPENAI_MODEL"),
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def require_configured(self) -> None:
        if not self.configured:
            raise RuntimeError(
                "LLM enhancement is not configured. Set SAGE_OPENAI_API_KEY and optionally "
                "SAGE_OPENAI_BASE_URL / SAGE_OPENAI_MODEL in the environment or a local .env "
                "file before using AI features.",
            )


class SageOpenAIClient:
    """Thin wrapper around an OpenAI-compatible endpoint."""

    def __init__(self, settings: SageOpenAISettings | None = None) -> None:
        self.settings = settings or SageOpenAISettings.from_env()
        self.settings.require_configured()
        if httpx is None or OpenAI is None:
            raise RuntimeError(
                "Missing LLM client dependencies. Ensure httpx and openai are installed.",
            )

        self._http_client = httpx.Client(headers={"User-Agent": DEFAULT_USER_AGENT}, timeout=30.0)
        self._client = OpenAI(
            base_url=self.settings.base_url,
            api_key=self.settings.api_key,
            http_client=self._http_client,
        )

    def list_models(self) -> list[str]:
        response = self._client.models.list()
        return [item.id for item in getattr(response, "data", [])]

    def _resolve_model(self) -> str:
        if self.settings.model:
            return self.settings.model
        model_ids = self.list_models()
        if not model_ids:
            raise RuntimeError("The configured OpenAI-compatible endpoint returned no models.")
        return model_ids[0]

    def generate_learning_guidance(
        self,
        *,
        student_profile: dict[str, Any],
        diagnosis: dict[str, Any],
        wrong_question_bank: list[dict[str, Any]],
        knowledge_graph: dict[str, Any],
    ) -> str:
        model_name = self._resolve_model()
        prompt_payload = {
            "student_profile": student_profile,
            "diagnosis": diagnosis,
            "wrong_question_bank": wrong_question_bank[:5],
            "knowledge_graph": {
                "nodes": knowledge_graph.get("nodes", []),
                "edges": knowledge_graph.get("edges", []),
            },
        }
        response = self._client.chat.completions.create(
            model=model_name,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是个性化提分系统的学情分析助手。请基于输入输出简洁、可执行、可解释的中文建议。"
                        "请分成三部分：1) 当前判断 2) 三条优先行动 3) 给学生的话。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt_payload, ensure_ascii=False, indent=2),
                },
            ],
        )
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise RuntimeError("LLM endpoint returned no completion choices.")

        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            text_chunks = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") in {"text", "output_text"}
            ]
            merged = "\n".join(chunk for chunk in text_chunks if chunk).strip()
            if merged:
                return merged

        raise RuntimeError("LLM endpoint returned an empty completion message.")
