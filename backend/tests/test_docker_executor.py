# backend/tests/test_docker_executor.py

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.docker_executor import DockerExecutor
from app.services.sandbox_config import (
    SANDBOX_IMAGE, SANDBOX_MEMORY_LIMIT, SANDBOX_CPU_LIMIT,
    SANDBOX_TIMEOUT_SECONDS, SANDBOX_MAX_OUTPUT_BYTES
)


# ── T1: Happy path — code passes all tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_passing_code_returns_success(
    mock_docker_proc_success,
    sample_code_passing,
    sample_test_code,
):
    """Container exits 0 → success:True, exit_code:0, timed_out:False."""
    executor = DockerExecutor()
    executor.available = True

    with patch("asyncio.create_subprocess_exec", return_value=mock_docker_proc_success):
        result = await executor.run_code_in_sandbox(
            code=sample_code_passing,
            test_code=sample_test_code,
        )

    assert result["success"] is True
    assert result["exit_code"] == 0
    assert result["timed_out"] is False
    assert result["error"] is None
    assert "passed" in result["stdout"].lower()
    assert isinstance(result["duration_ms"], float)
    assert result["duration_ms"] >= 0


# ── T2: Failing test — assertion error from pytest ────────────────────────────

@pytest.mark.asyncio
async def test_failing_test_returns_failure(
    mock_docker_proc_failure,
    sample_code_failing,
    sample_test_code_failing,
):
    """Container exits 1 → success:False, exit_code:1, stderr contains failure info."""
    executor = DockerExecutor()
    executor.available = True

    with patch("asyncio.create_subprocess_exec", return_value=mock_docker_proc_failure):
        result = await executor.run_code_in_sandbox(
            code=sample_code_failing,
            test_code=sample_test_code_failing,
        )

    assert result["success"] is False
    assert result["exit_code"] == 1
    assert result["timed_out"] is False
    assert result["error"] is None
    # stdout should contain pytest failure output
    assert "FAILED" in result["stdout"] or "AssertionError" in result["stdout"]


# ── T3: Syntax error — Python cannot even parse the file ──────────────────────

@pytest.mark.asyncio
async def test_syntax_error_returns_failure_with_stderr(
    mock_docker_proc_syntax_error,
    sample_code_syntax_error,
    sample_test_code,
):
    """SyntaxError in code → exit_code non-zero, stderr contains SyntaxError."""
    executor = DockerExecutor()
    executor.available = True

    with patch("asyncio.create_subprocess_exec", return_value=mock_docker_proc_syntax_error):
        result = await executor.run_code_in_sandbox(
            code=sample_code_syntax_error,
            test_code=sample_test_code,
        )

    assert result["success"] is False
    assert result["exit_code"] != 0
    assert "SyntaxError" in result["stderr"]
    assert result["timed_out"] is False


# ── T4: Timeout — infinite loop code hits timeout ─────────────────────────────

@pytest.mark.asyncio
async def test_infinite_loop_triggers_timeout():
    """asyncio.TimeoutError raised → timed_out:True, success:False."""
    executor = DockerExecutor()
    executor.available = True

    proc = AsyncMock()
    proc.returncode = None
    proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
    proc.kill = MagicMock()

    with patch("asyncio.create_subprocess_exec", return_value=proc):
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            result = await executor.run_code_in_sandbox(
                code="while True: pass",
                test_code="def test_x(): pass",
                timeout_seconds=1,
            )

    assert result["timed_out"] is True
    assert result["success"] is False
    assert result["exit_code"] != 0


# ── T5: Docker unavailable — graceful degradation ────────────────────────────

@pytest.mark.asyncio
async def test_docker_unavailable_returns_error_dict(mock_docker_unavailable):
    """If Docker CLI not found, return error dict without raising."""
    executor = DockerExecutor()
    executor.available = False  # simulates health_check() returning False

    result = await executor.run_code_in_sandbox(
        code="def add(a,b): return a+b",
        test_code="from main import add\ndef test_add(): assert add(1,1)==2",
    )

    assert result["success"] is False
    assert result["error"] is not None
    assert "docker" in result["error"].lower() or "not available" in result["error"].lower()
    assert result["exit_code"] == -1
    assert result["timed_out"] is False


# ── T6: Output truncation ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stdout_is_truncated_at_max_output_bytes():
    """Stdout larger than SANDBOX_MAX_OUTPUT_BYTES must be truncated with [TRUNCATED] appended."""
    executor = DockerExecutor()
    executor.available = True

    huge_output = b"x" * (SANDBOX_MAX_OUTPUT_BYTES + 5000)

    proc = AsyncMock()
    proc.returncode = 0
    proc.communicate = AsyncMock(return_value=(huge_output, b""))

    with patch("asyncio.create_subprocess_exec", return_value=proc):
        result = await executor.run_code_in_sandbox(
            code="print('x' * 2_000_000)",
            test_code="def test_x(): pass",
        )

    assert len(result["stdout"]) <= SANDBOX_MAX_OUTPUT_BYTES + 50  # small buffer for the tag
    assert "[TRUNCATED]" in result["stdout"]


# ── T7: Docker CLI flags — security config verified ──────────────────────────

@pytest.mark.asyncio
async def test_docker_run_command_includes_security_flags(
    mock_docker_proc_success,
    sample_code_passing,
    sample_test_code,
):
    """
    The command passed to asyncio.create_subprocess_exec must include
    all mandatory security flags. This test captures the actual call args.
    """
    executor = DockerExecutor()
    executor.available = True

    captured_args = []

    async def fake_subprocess(*args, **kwargs):
        captured_args.extend(args)
        return mock_docker_proc_success

    with patch("asyncio.create_subprocess_exec", side_effect=fake_subprocess):
        await executor.run_code_in_sandbox(
            code=sample_code_passing,
            test_code=sample_test_code,
        )

    cmd_str = " ".join(str(a) for a in captured_args)
    assert "--network none" in cmd_str, "Missing --network none"
    assert "--memory" in cmd_str, "Missing --memory flag"
    assert "--cpus" in cmd_str, "Missing --cpus flag"
    assert "--user" in cmd_str, "Missing --user flag"
    assert ":ro" in cmd_str, "Volume mount must be read-only (:ro)"
    assert SANDBOX_IMAGE in cmd_str, f"Expected image {SANDBOX_IMAGE} in command"


# ── T8: health_check — Docker available ───────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check_returns_true_when_docker_available():
    """If `docker info` exits 0, health_check() returns True."""
    executor = DockerExecutor()

    proc = AsyncMock()
    proc.returncode = 0
    proc.communicate = AsyncMock(return_value=(b"Server: Docker Engine", b""))

    with patch("asyncio.create_subprocess_exec", return_value=proc):
        result = await executor.health_check()

    assert result is True


# ── T9: health_check — Docker not installed ───────────────────────────────────

@pytest.mark.asyncio
async def test_health_check_returns_false_when_docker_missing():
    """If `docker info` raises FileNotFoundError, health_check() returns False (no raise)."""
    executor = DockerExecutor()

    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError("docker: command not found")):
        result = await executor.health_check()

    assert result is False
