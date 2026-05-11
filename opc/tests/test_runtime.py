from pathlib import Path
import os
import signal
import subprocess
import sys
import time


ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from opc.runtime import LaunchConfig, RunningInstance, ProcessRuntimeAdapter


def test_process_watcher_does_not_mark_intentional_stop_as_error() -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    adapter = ProcessRuntimeAdapter(
        ROOT_DIR,
        python_executable=sys.executable,
        port_range_start=19000,
        port_range_end=19010,
    )
    instance = RunningInstance(
        instance_id="test-stop",
        app_id="ticket_triage_api",
        app_name="Ticket Triage API",
        host="127.0.0.1",
        port=19000,
        working_dir=str(ROOT_DIR),
        command=[sys.executable],
        env={},
        launch_config=LaunchConfig(),
        endpoint=None,
        app_ui_url=None,
        status="stopping",
        pid=process.pid,
        process=process,
    )

    adapter._start_process_watcher(instance)
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)

    deadline = time.time() + 5
    while time.time() < deadline and instance.exit_code is None:
        time.sleep(0.05)

    assert instance.status == "stopped"
    assert instance.exit_code is not None
    assert instance.last_error is None