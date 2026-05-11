from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from opc.discovery import discover_apps, get_app_definition


def test_discovery_includes_verified_ticket_triage_api() -> None:
    app = get_app_definition(ROOT_DIR, "ticket_triage_api")

    assert app.verified is True
    assert app.verification_status == "verified"
    assert app.port.default == 8010
    assert app.web_ui.starts_own_ui is True
    assert app.health_path == "/health"

    command = app.build_command(
        "/root/miniconda3/envs/sage/bin/python",
        ROOT_DIR,
        host="127.0.0.1",
        port=18010,
        storage_path=ROOT_DIR / ".sage" / "ticket-triage.json",
    )

    assert "--host" in command
    assert "--port" in command
    assert "18010" in command
    assert "--storage-path" in command

    environment = app.build_environment(ROOT_DIR)
    assert str((ROOT_DIR / "apps/src").resolve()) in environment["PYTHONPATH"]


def test_discovery_scans_example_scripts() -> None:
    app_ids = {app.id for app in discover_apps(ROOT_DIR)}

    assert "traffic_briefing" in app_ids
    assert "ticket_triage_api" in app_ids
    assert "supply_chain_alert_api" in app_ids


def test_discovery_extracts_required_args_for_batch_pipeline() -> None:
    app = get_app_definition(ROOT_DIR, "data_cleaner")

    required_args = {argument.primary_name for argument in app.arguments if argument.required}
    input_argument = next(argument for argument in app.arguments if argument.primary_name == "--input")
    output_argument = next(argument for argument in app.arguments if argument.primary_name == "--output")

    assert app.execution_mode == "batch"
    assert "--input" in required_args
    assert "--output" in required_args
    assert app.filesystem.requires_workspace is True
    assert input_argument.opc_default_value is not None
    assert Path(input_argument.opc_default_value).exists()
    assert output_argument.opc_default_value is not None


def test_discovery_refreshes_generated_samples_with_topic_aware_content() -> None:
    app = get_app_definition(ROOT_DIR, "company_credit")
    input_argument = next(argument for argument in app.arguments if argument.primary_name == "--input-file")

    assert input_argument.opc_default_value is not None
    sample_path = Path(input_argument.opc_default_value)
    assert sample_path.exists()
    content = sample_path.read_text(encoding="utf-8")
    assert "Blue Harbor" in content
    assert "cash pressure" in content


def test_discovery_marks_conservative_llm_related_apps() -> None:
    app = get_app_definition(ROOT_DIR, "work_report")

    assert "llm" in app.tags


def test_discovery_extracts_env_vars_and_examples() -> None:
    app = get_app_definition(ROOT_DIR, "work_report")

    assert "GITHUB_TOKEN" in app.environment_variables
    assert any("--no-submodules" in example for example in app.examples)
    assert app.usage is not None