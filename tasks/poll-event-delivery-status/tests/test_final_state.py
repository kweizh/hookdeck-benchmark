import os
import re
import subprocess
import time

import pytest

SCRIPT_PATH = "/workspace/await_delivery.py"
SEEDED_ENV_FILE = "/workspace/.seeded_events.env"
SUCCESS_LOG = "/workspace/await_success.log"
FAILURE_LOG = "/workspace/await_failure.log"


def _parse_env_file(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :]
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("'").strip('"')
            values[key] = val
    return values


@pytest.fixture(scope="module")
def seeded_env() -> dict[str, str]:
    assert os.path.isfile(SEEDED_ENV_FILE), (
        f"Seeded event ids file {SEEDED_ENV_FILE} does not exist."
    )
    return _parse_env_file(SEEDED_ENV_FILE)


@pytest.fixture(autouse=True)
def _cleanup_logs():
    for log_path in (SUCCESS_LOG, FAILURE_LOG):
        if os.path.exists(log_path):
            os.remove(log_path)
    yield


def _run_script(event_id: str) -> tuple[int, str, str, float]:
    env = os.environ.copy()
    env["EVENT_ID"] = event_id
    start = time.monotonic()
    proc = subprocess.run(
        ["python3", SCRIPT_PATH],
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
    elapsed = time.monotonic() - start
    return proc.returncode, proc.stdout, proc.stderr, elapsed


def test_await_delivery_script_exists():
    assert os.path.isfile(SCRIPT_PATH), (
        f"Expected the await delivery script at {SCRIPT_PATH}, but it was not found."
    )


def test_successful_event_exits_zero(seeded_env: dict[str, str]):
    event_id = seeded_env["SUCCESSFUL_EVENT_ID"]
    returncode, stdout, stderr, _ = _run_script(event_id)
    with open(SUCCESS_LOG, "w") as f:
        f.write(stdout)
        if stderr:
            f.write("\n--- STDERR ---\n")
            f.write(stderr)
    assert returncode == 0, (
        f"Expected exit code 0 for SUCCESSFUL event {event_id}, "
        f"got {returncode}. stdout={stdout!r} stderr={stderr!r}"
    )


def test_successful_event_prints_attempt_count(seeded_env: dict[str, str]):
    event_id = seeded_env["SUCCESSFUL_EVENT_ID"]
    returncode, stdout, stderr, _ = _run_script(event_id)
    assert returncode == 0, (
        f"Expected exit code 0 for SUCCESSFUL event {event_id}, got {returncode}. "
        f"stdout={stdout!r} stderr={stderr!r}"
    )
    matches = re.findall(r"^attempt_count=([1-9][0-9]*)$", stdout, flags=re.MULTILINE)
    assert matches, (
        f"Expected stdout to contain a line like 'attempt_count=<positive int>'. "
        f"Got stdout={stdout!r}"
    )


def test_successful_event_prints_response_status_200(seeded_env: dict[str, str]):
    event_id = seeded_env["SUCCESSFUL_EVENT_ID"]
    returncode, stdout, stderr, _ = _run_script(event_id)
    assert returncode == 0, (
        f"Expected exit code 0 for SUCCESSFUL event {event_id}, got {returncode}. "
        f"stdout={stdout!r} stderr={stderr!r}"
    )
    assert re.search(r"^response_status=200$", stdout, flags=re.MULTILINE), (
        f"Expected stdout to contain 'response_status=200' on its own line. "
        f"Got stdout={stdout!r}"
    )


def test_failed_event_exits_nonzero(seeded_env: dict[str, str]):
    event_id = seeded_env["FAILED_EVENT_ID"]
    returncode, stdout, stderr, elapsed = _run_script(event_id)
    with open(FAILURE_LOG, "w") as f:
        f.write(stdout)
        if stderr:
            f.write("\n--- STDERR ---\n")
            f.write(stderr)
    assert returncode != 0, (
        f"Expected non-zero exit code for FAILED event {event_id}, "
        f"got 0. stdout={stdout!r} stderr={stderr!r}"
    )
    # The polling budget is 30 seconds; allow a small startup tolerance.
    assert elapsed <= 35, (
        f"The script took {elapsed:.2f}s for the FAILED event, which exceeds the "
        f"30s polling budget plus tolerance. Backoff/timeout enforcement appears broken."
    )


def test_failed_event_prints_attempt_count(seeded_env: dict[str, str]):
    event_id = seeded_env["FAILED_EVENT_ID"]
    returncode, stdout, stderr, _ = _run_script(event_id)
    assert returncode != 0, (
        f"Expected non-zero exit code for FAILED event {event_id}, got 0. "
        f"stdout={stdout!r} stderr={stderr!r}"
    )
    matches = re.findall(r"^attempt_count=([1-9][0-9]*)$", stdout, flags=re.MULTILINE)
    assert matches, (
        f"Expected stdout to contain a line like 'attempt_count=<positive int>' for the FAILED event. "
        f"Got stdout={stdout!r}"
    )


def test_failed_event_prints_upstream_response_status(seeded_env: dict[str, str]):
    event_id = seeded_env["FAILED_EVENT_ID"]
    returncode, stdout, stderr, _ = _run_script(event_id)
    assert returncode != 0, (
        f"Expected non-zero exit code for FAILED event {event_id}, got 0. "
        f"stdout={stdout!r} stderr={stderr!r}"
    )
    assert re.search(r"^response_status=(4[0-9]{2}|5[0-9]{2})$", stdout, flags=re.MULTILINE), (
        f"Expected stdout to contain 'response_status=<4xx or 5xx>' on its own line "
        f"reflecting the upstream failure. Got stdout={stdout!r}"
    )
