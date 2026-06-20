# backend/tests/conftest.py

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from main import app  # Imported from backend/main.py


# ─── Event Loop ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ─── FastAPI Test Client ───────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def async_client():
    """Async HTTP client wired to the FastAPI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# ─── Mock Docker Subprocess ───────────────────────────────────────────────────

@pytest.fixture
def mock_docker_proc_success():
    """
    Simulates a Docker subprocess that exits 0 with pytest-style passing output.
    Use this when testing happy-path sandbox runs.
    """
    proc = AsyncMock()
    proc.returncode = 0
    proc.communicate = AsyncMock(return_value=(
        b"============================= test session starts ==============================\n"
        b"collected 2 items\n\n"
        b"test_main.py::test_add PASSED\n"
        b"test_main.py::test_subtract PASSED\n\n"
        b"============================== 2 passed in 0.12s ==============================\n",
        b""  # stderr empty on success
    ))
    return proc


@pytest.fixture
def mock_docker_proc_failure():
    """
    Simulates a Docker subprocess that exits 1 with pytest failure output.
    Use this when testing failure detection and healing trigger.
    """
    proc = AsyncMock()
    proc.returncode = 1
    proc.communicate = AsyncMock(return_value=(
        b"============================= test session starts ==============================\n"
        b"collected 1 item\n\n"
        b"test_main.py::test_add FAILED\n\n"
        b"================================== FAILURES ===================================\n"
        b"_________________________________ test_add ___________________________________\n\n"
        b"    def test_add():\n"
        b">       assert add(2, 2) == 5\n"
        b"E       AssertionError: assert 4 == 5\n\n"
        b"test_main.py:4: AssertionError\n"
        b"============================== 1 failed in 0.08s ==============================\n",
        b"",
    ))
    return proc


@pytest.fixture
def mock_docker_proc_syntax_error():
    """Simulates a container where the code itself has a Python syntax error."""
    proc = AsyncMock()
    proc.returncode = 1
    proc.communicate = AsyncMock(return_value=(
        b"",
        b"  File \"/sandbox/main.py\", line 3\n"
        b"    def broken(\n"
        b"              ^\n"
        b"SyntaxError: unexpected EOF while parsing\n",
    ))
    return proc


@pytest.fixture
def mock_docker_unavailable():
    """
    Simulates the host not having Docker installed.
    asyncio.create_subprocess_exec raises FileNotFoundError.
    """
    async def raise_not_found(*args, **kwargs):
        raise FileNotFoundError("docker: command not found")
    return raise_not_found


# ─── Sample Task Data ──────────────────────────────────────────────────────────

@pytest.fixture
def sample_task_id():
    return "task-test-phase9-001"


@pytest.fixture
def sample_code_passing():
    return (
        "def add(a, b):\n"
        "    return a + b\n\n"
        "def subtract(a, b):\n"
        "    return a - b\n"
    )


@pytest.fixture
def sample_code_failing():
    return (
        "def add(a, b):\n"
        "    return a - b  # deliberate bug\n"
    )


@pytest.fixture
def sample_code_syntax_error():
    return (
        "def broken(\n"
        "    # missing closing paren and body\n"
    )


@pytest.fixture
def sample_test_code():
    return (
        "from main import add, subtract\n\n"
        "def test_add():\n"
        "    assert add(2, 2) == 4\n\n"
        "def test_subtract():\n"
        "    assert subtract(5, 3) == 2\n"
    )


@pytest.fixture
def sample_test_code_failing():
    return (
        "from main import add\n\n"
        "def test_add():\n"
        "    assert add(2, 2) == 5  # wrong expected value\n"
    )


# ─── Sample Graph ─────────────────────────────────────────────────────────────

@pytest.fixture
def sample_graph_coder_tester():
    """Minimal graph: CoderAgent \u2192 TesterAgent."""
    return {
        "nodes": [
            {"id": "node-coder-1", "type": "CoderAgent", "data": {"label": "Coder"}, "position": {"x": 0, "y": 0}},
            {"id": "node-tester-1", "type": "TesterAgent", "data": {"label": "Tester"}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [
            {"id": "edge-1", "source": "node-coder-1", "target": "node-tester-1", "data": {}},
        ],
    }


@pytest.fixture
def sample_graph_full_pipeline():
    """Full graph: Planner \u2192 Coder \u2192 Tester \u2192 Debugger \u2192 Reviewer."""
    return {
        "nodes": [
            {"id": "node-planner", "type": "PlannerAgent", "data": {"label": "Planner"}, "position": {"x": 0, "y": 0}},
            {"id": "node-coder", "type": "CoderAgent", "data": {"label": "Coder"}, "position": {"x": 200, "y": 0}},
            {"id": "node-tester", "type": "TesterAgent", "data": {"label": "Tester"}, "position": {"x": 400, "y": 0}},
            {"id": "node-debugger", "type": "DebuggerAgent", "data": {"label": "Debugger"}, "position": {"x": 600, "y": 0}},
            {"id": "node-reviewer", "type": "ReviewerAgent", "data": {"label": "Reviewer"}, "position": {"x": 800, "y": 0}},
        ],
        "edges": [
            {"id": "e1", "source": "node-planner", "target": "node-coder", "data": {}},
            {"id": "e2", "source": "node-coder", "target": "node-tester", "data": {}},
            {"id": "e3", "source": "node-tester", "target": "node-debugger", "data": {}},
            {"id": "e4", "source": "node-debugger", "target": "node-reviewer", "data": {}},
        ],
    }
