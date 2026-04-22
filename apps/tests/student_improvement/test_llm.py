import pytest

from sage.apps.student_improvement.app import StudentImprovementConsoleApp
from sage.apps.student_improvement.llm import SageOpenAISettings


def test_llm_settings_from_env(monkeypatch) -> None:
    monkeypatch.setenv("SAGE_OPENAI_BASE_URL", "https://api.sage.org.ai/v1")
    monkeypatch.setenv("SAGE_OPENAI_API_KEY", "test-key")  # pragma: allowlist secret
    monkeypatch.setenv("SAGE_OPENAI_MODEL", "demo-model")

    settings = SageOpenAISettings.from_env()

    assert settings.base_url == "https://api.sage.org.ai/v1"
    assert settings.api_key == "test-key"  # pragma: allowlist secret
    assert settings.model == "demo-model"
    assert settings.configured is True


def test_llm_settings_require_configured(monkeypatch) -> None:
    monkeypatch.delenv("SAGE_OPENAI_API_KEY", raising=False)

    settings = SageOpenAISettings.from_env()

    with pytest.raises(RuntimeError, match="LLM enhancement is not configured"):
        settings.require_configured()


def test_llm_settings_from_dotenv(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SAGE_OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("SAGE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SAGE_OPENAI_MODEL", raising=False)
    (tmp_path / ".env").write_text(
        "SAGE_OPENAI_BASE_URL=https://api.sage.org.ai/v1\n"
        "SAGE_OPENAI_API_KEY=dotenv-key\n"  # pragma: allowlist secret
        "SAGE_OPENAI_MODEL=dotenv-model\n",
        encoding="utf-8",
    )

    settings = SageOpenAISettings.from_env()

    assert settings.base_url == "https://api.sage.org.ai/v1"
    assert settings.api_key == "dotenv-key"  # pragma: allowlist secret
    assert settings.model == "dotenv-model"
    assert settings.configured is True


def test_console_app_imports_next_demo_exam(tmp_path) -> None:
    app = StudentImprovementConsoleApp(storage_path=tmp_path / "student-state.json")

    imported = app.import_next_demo_exam(render=False)

    assert imported is not None
    result_payload, graph_payload = imported
    assert result_payload["exam_id"] == "exam-2026-01"
    assert graph_payload["student_id"] == "stu-demo-001"
    assert app.session_results
