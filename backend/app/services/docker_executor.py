# backend/app/services/docker_executor.py

import os
import sys
import shutil
import tempfile
import time
import asyncio
import logging
from uuid import uuid4

from app.services.sandbox_config import (
    SANDBOX_IMAGE,
    SANDBOX_MEMORY_LIMIT,
    SANDBOX_CPU_LIMIT,
    SANDBOX_TIMEOUT_SECONDS,
    SANDBOX_USER,
    SANDBOX_MAX_OUTPUT_BYTES
)

logger = logging.getLogger("sync.docker_executor")

# Docker installation requirement: Docker CLI must be installed and running on the host machine.
class DockerExecutor:
    def __init__(self):
        self.available = True
        # Schedule startup check once event loop runs
        if "pytest" not in sys.modules:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self._startup_health_check())
            except RuntimeError:
                pass

    async def _startup_health_check(self):
        self.available = await self.health_check()
        if not self.available:
            logger.error("Docker is not available on this host. Sandbox runs will fall back.")

    async def health_check(self) -> bool:
        """Verify Docker daemon is accessible."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "info",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return proc.returncode == 0
        except Exception as e:
            logger.error(f"Docker health check failed: {e}")
            return False

    async def run_code_in_sandbox(
        self,
        code: str,
        test_code: str,
        language: str = "python",
        timeout_seconds: int = 30,
    ) -> dict:
        """Run code inside a sandboxed Docker container."""
        # Double check availability (if not checked yet or explicitly false)
        if not self.available:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "timed_out": False,
                "error": "Docker is not available on this host",
                "duration_ms": 0.0,
            }

        start_time = time.time()
        tmp_dir = tempfile.mkdtemp()
        container_name = f"sync_sandbox_{uuid4().hex[:8]}"

        # Write files
        try:
            main_path = os.path.join(tmp_dir, "main.py")
            test_path = os.path.join(tmp_dir, "test_main.py")

            with open(main_path, "w", encoding="utf-8") as f:
                f.write(code)

            with open(test_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            # Ensure host path is formatted cleanly for docker mount on Windows
            host_mount_dir = os.path.abspath(tmp_dir)

            cmd = [
                "docker", "run",
                "--rm",
                "--name", container_name,
                "--network", "none",
                "--memory", SANDBOX_MEMORY_LIMIT,
                "--memory-swap", SANDBOX_MEMORY_LIMIT,
                "--cpus", SANDBOX_CPU_LIMIT,
                "--user", SANDBOX_USER,
                "-v", f"{host_mount_dir}:/sandbox:ro",
                "-w", "/sandbox",
                SANDBOX_IMAGE,
                "python", "-m", "pytest", "test_main.py", "-v", "--tb=short"
            ]

            logger.info(f"Starting sandbox run {container_name}")
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout_seconds
                )
                timed_out = False
                exit_code = proc.returncode
            except asyncio.TimeoutError:
                timed_out = True
                exit_code = -1
                logger.warning(f"Sandbox run {container_name} timed out. Killing container.")
                # Kill container
                try:
                    kill_proc = await asyncio.create_subprocess_exec(
                        "docker", "kill", container_name,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                    await kill_proc.wait()
                except Exception as ke:
                    logger.error(f"Failed to kill timed out container {container_name}: {ke}")
                stdout_bytes, stderr_bytes = b"", b"Execution timed out"

            duration_ms = (time.time() - start_time) * 1000.0

            # Decode
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            # Truncate if exceeds max size
            if len(stdout) > SANDBOX_MAX_OUTPUT_BYTES:
                stdout = stdout[:SANDBOX_MAX_OUTPUT_BYTES] + "\n[TRUNCATED]"
            if len(stderr) > SANDBOX_MAX_OUTPUT_BYTES:
                stderr = stderr[:SANDBOX_MAX_OUTPUT_BYTES] + "\n[TRUNCATED]"

            success = (exit_code == 0) and not timed_out

            logger.info(f"Finished sandbox run {container_name} in {duration_ms:.1f}ms (success={success})")

            return {
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "timed_out": timed_out,
                "error": None,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            logger.error(f"Failed to run code in sandbox: {e}")
            duration_ms = (time.time() - start_time) * 1000.0
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "timed_out": False,
                "error": str(e),
                "duration_ms": duration_ms,
            }

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

docker_executor = DockerExecutor()
