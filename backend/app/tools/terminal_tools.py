import asyncio
from datetime import datetime

BLOCKED_PATTERNS = [
    "rm -rf /",
    "shutdown",
    "reboot",
    "format",
    "del /f /s /q c:\\",
    "mkfs",
    ":(){:|:&};:",
    "chmod 777 /",
    "curl | bash",
    "wget | sh",
]

TIMEOUT_SECONDS = 60


async def run_command(command: str, cwd: str = "workspace") -> dict:
    """Run a shell command inside the workspace directory."""
    start = datetime.utcnow()

    cmd_lower = command.lower()
    for blocked in BLOCKED_PATTERNS:
        if blocked in cmd_lower:
            return {
                "success": False,
                "tool": "run_command",
                "error": f"Blocked command pattern: {blocked}",
            }

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            proc.kill()
            return {
                "success": False,
                "tool": "run_command",
                "error": f"Command timed out after {TIMEOUT_SECONDS}s",
            }

        ms = (datetime.utcnow() - start).microseconds // 1000
        return {
            "success": proc.returncode == 0,
            "tool": "run_command",
            "return_code": proc.returncode,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "execution_time_ms": ms,
        }
    except Exception as e:
        return {"success": False, "tool": "run_command", "error": str(e)}
