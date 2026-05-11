import json
from pathlib import Path
import sys
import time

from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from opc.server import create_app


def test_apps_endpoint_returns_catalog() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable=sys.executable))

    response = client.get("/api/apps")

    assert response.status_code == 200
    payload = response.json()
    assert any(app["id"] == "ticket_triage_api" for app in payload["apps"])


def test_validate_endpoint_returns_command_preview() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    response = client.post(
        "/api/apps/ticket_triage_api/validate",
        json={
            "auto_port": False,
            "port": 18999,
            "storage_path": str(ROOT_DIR / ".sage" / "opc-ticket-triage-test.json"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["resolved_port"] == 18999
    assert "run_ticket_triage_api.py" in payload["command_preview"]
    assert payload["app_ui_preview"].endswith("/dashboard/ui")
    assert any(check["name"] == "script_exists" and check["passed"] for check in payload["checks"])


def test_validate_endpoint_autofills_default_required_cli_args() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    response = client.post(
        "/api/apps/data_cleaner/validate",
        json={"auto_port": True},
    )

    assert response.status_code == 200
    payload = response.json()
    required_check = next(
        check for check in payload["checks"] if check["name"] == "required_arguments_present"
    )
    assert required_check["passed"] is True
    assert any(token.endswith(".sage/opc-default-inputs/data_cleaner/raw.csv") for token in payload["command"])
    assert any(".sage/opc-default-outputs/data_cleaner/" in token and token.endswith((".csv", ".json", ".txt")) for token in payload["command"])


def test_invoke_endpoint_supports_inline_source_for_batch_pipeline() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    response = client.post(
        "/api/apps/data_cleaner/invoke",
        json={
            "source": "name,age\nAlice,30\nBob,\n",
            "source_filename": "customers.csv",
            "extra_args": ["--fill-strategy", "drop", "--output-format", "json"],
            "timeout_seconds": 20,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["return_code"] == 0
    assert payload["materialized_inputs"][0]["argument"] == "--input"
    assert payload["output_artifacts"]
    assert payload["output_artifacts"][0]["exists"] is True
    assert "Alice" in payload["output_artifacts"][0].get("content_preview", "")
    assert payload["metrics_path"].endswith("metrics.json")
    assert payload["metrics"]["status"] == "completed"
    assert payload["metrics"]["pipeline_stage_count"] >= 1
    assert any(stage["avg_latency_ms"] is not None for stage in payload["metrics"]["stages"])


def test_launch_service_mode_registers_instance_invoke_endpoint() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    response = client.post(
        "/api/apps/data_cleaner/launch",
        json={
            "service_mode": True,
            "extra_args": ["--fill-strategy", "drop", "--output-format", "json"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["service_mode"] is True
    assert payload["status"] == "running"
    assert payload["invoke_path"].startswith("/api/instances/")


def test_service_mode_instance_accepts_prompt_like_invoke_requests() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    launch = client.post(
        "/api/apps/data_cleaner/launch",
        json={
            "service_mode": True,
            "extra_args": ["--fill-strategy", "drop", "--output-format", "json"],
        },
    )
    instance = launch.json()

    response = client.post(
        instance["invoke_path"],
        json={
            "prompt": "name,age\nAlice,30\nBob,\n",
            "prompt_filename": "customers.csv",
            "timeout_seconds": 20,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["return_code"] == 0
    assert payload["materialized_inputs"][0]["argument"] == "--input"
    assert payload["output_artifacts"][0]["exists"] is True
    assert payload["metrics"]["status"] == "completed"

    detail = client.get(f"/api/instances/{instance['instance_id']}")

    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["metrics"]["status"] == "completed"
    assert detail_payload["last_result"]["metrics_path"].endswith("metrics.json")
    assert detail_payload["last_result"]["output_artifacts"][0]["exists"] is True


def test_openai_models_lists_service_instances() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    launched = client.post(
        "/api/apps/data_cleaner/launch",
        json={
            "service_mode": True,
            "extra_args": ["--fill-strategy", "drop", "--output-format", "json"],
        },
    ).json()

    response = client.get("/v1/models")

    assert response.status_code == 200
    payload = response.json()
    assert any(model["id"] == launched["openai_model"] for model in payload["data"])


def test_openai_chat_completions_runs_service_instance() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    launched = client.post(
        "/api/apps/data_cleaner/launch",
        json={
            "service_mode": True,
            "extra_args": ["--fill-strategy", "drop", "--output-format", "json"],
        },
    ).json()

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": launched["openai_model"],
            "messages": [{"role": "user", "content": "name,age\nAlice,30\nBob,\n"}],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == launched["openai_model"]
    assert payload["choices"][0]["message"]["role"] == "assistant"
    assert "Alice" in payload["choices"][0]["message"]["content"]


def test_openai_completions_runs_service_instance() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    launched = client.post(
        "/api/apps/data_cleaner/launch",
        json={
            "service_mode": True,
            "extra_args": ["--fill-strategy", "drop", "--output-format", "json"],
        },
    ).json()

    response = client.post(
        "/v1/completions",
        json={
            "model": launched["openai_model"],
            "prompt": "name,age\nAlice,30\nBob,\n",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == launched["openai_model"]
    assert "Alice" in payload["choices"][0]["text"]


def test_batch_launch_completes_instead_of_showing_stopped() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    launched = client.post(
        "/api/apps/company_credit/launch",
        json={"auto_port": True},
    )

    assert launched.status_code == 200
    instance_id = launched.json()["instance_id"]

    deadline = time.time() + 5
    final_payload = None
    while time.time() < deadline:
        detail = client.get(f"/api/instances/{instance_id}")
        assert detail.status_code == 200
        final_payload = detail.json()
        if final_payload["status"] in {"completed", "failed"}:
            break
        time.sleep(0.05)

    assert final_payload is not None
    assert final_payload["status"] == "completed"
    assert final_payload["exit_code"] == 0
    assert final_payload["metrics_path"].endswith("metrics.json")
    assert final_payload["metrics"]["status"] == "completed"
    assert final_payload["metrics"]["stages"]


def test_running_http_instance_refreshes_metrics_from_artifact() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    launched = client.post(
        "/api/apps/ticket_triage_api/launch",
        json={"auto_port": True},
    )

    assert launched.status_code == 200
    instance = launched.json()
    metrics_path = Path(instance["metrics_path"])
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(
            {
                "schema_version": "sage.local.operator.metrics.v1",
                "status": "completed",
                "pipeline_stage_count": 1,
                "source_stage_count": 1,
                "wall_time_ms": 12.5,
                "stages": [
                    {
                        "stage_name": "DemoTicketSource",
                        "op_type": "source",
                        "parallelism": 1,
                        "invocations": 1,
                        "input_items": 1,
                        "output_items": 1,
                        "errors": 0,
                        "total_duration_ms": 12.5,
                        "avg_latency_ms": 12.5,
                        "p95_latency_ms": 12.5,
                        "throughput_items_per_sec": 80.0,
                        "last_queue_depth": 0,
                        "max_queue_depth": 0,
                        "upstreams": [],
                        "downstreams": [],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    detail = client.get(f"/api/instances/{instance['instance_id']}")

    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["metrics"]["status"] == "completed"
    assert detail_payload["metrics"]["pipeline_stage_count"] == 1

    instances = client.get("/api/instances")

    assert instances.status_code == 200
    listed = next(
        item
        for item in instances.json()["instances"]
        if item["instance_id"] == instance["instance_id"]
    )
    assert listed["metrics"]["pipeline_stage_count"] == 1


def test_running_http_instance_demo_run_captures_metrics() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    launched = client.post(
        "/api/apps/ticket_triage_api/launch",
        json={
            "auto_port": True,
            "storage_path": str(ROOT_DIR / ".sage" / f"opc-ticket-triage-demo-{time.time_ns()}.json"),
        },
    )

    assert launched.status_code == 200
    instance = launched.json()

    demo = client.post(f"/api/instances/{instance['instance_id']}/demo-run")

    assert demo.status_code == 200
    payload = demo.json()
    assert payload["success"] is True
    assert payload["http_status"] == 200
    assert payload["metrics_path"].endswith("metrics.json")
    assert payload["metrics"]["status"] == "completed"
    assert payload["metrics"]["pipeline_stage_count"] >= 1
    assert payload["metrics"]["stages"]
    assert payload["response_json"]["processed_event_count"] >= 1

    detail = client.get(f"/api/instances/{instance['instance_id']}")

    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["metrics"]["status"] == "completed"
    assert detail_payload["last_result"]["http_status"] == 200
    assert detail_payload["last_result"]["response_json"]["processed_event_count"] >= 1


def test_experiments_endpoint_collects_runtime_actions() -> None:
    client = TestClient(create_app(root_dir=ROOT_DIR, python_executable="/root/miniconda3/envs/sage/bin/python"))

    launched = client.post(
        "/api/apps/data_cleaner/launch",
        json={
            "service_mode": True,
            "extra_args": ["--fill-strategy", "drop", "--output-format", "json"],
        },
    ).json()

    compatibility = client.post(f"/api/instances/{launched['instance_id']}/compatibility")
    stop_response = client.post(f"/api/instances/{launched['instance_id']}/stop")
    experiments = client.get("/api/experiments")

    assert compatibility.status_code == 200
    assert stop_response.status_code == 200
    assert experiments.status_code == 200

    payload = experiments.json()
    assert payload["summary"]["total_events"] >= 3
    assert payload["summary"]["launches"] >= 1
    assert payload["summary"]["control_actions"] >= 2
    assert {record["kind"] for record in payload["records"]} >= {"launch", "compatibility", "stop"}

    reset = client.post("/api/experiments/reset")

    assert reset.status_code == 200
    assert reset.json()["summary"]["total_events"] == 0