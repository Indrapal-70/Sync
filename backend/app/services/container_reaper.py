import asyncio
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger("sync.container_reaper")


class ContainerReaper:
    def __init__(self):
        self._running = False
        self._task = None

    async def start(self, interval_seconds: int = 10, max_age_seconds: int = 300):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop(interval_seconds, max_age_seconds))
        logger.info("ContainerReaper started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("ContainerReaper stopped")

    async def _run_loop(self, interval_seconds: int, max_age_seconds: int):
        while self._running:
            try:
                await self.reap_containers(max_age_seconds)
            except Exception as e:
                logger.error(f"Error in ContainerReaper loop: {e}")
            await asyncio.sleep(interval_seconds)

    async def reap_containers(self, max_age_seconds: int = 300):
        """Find and remove container running longer than max_age_seconds with label sync.managed=true."""
        try:
            from app.services.docker_executor import docker_executor
            if not docker_executor.available:
                return

            # Get list of container IDs with label sync.managed=true
            proc = await asyncio.create_subprocess_exec(
                "docker", "ps", "-a", "--filter", "label=sync.managed=true", "--format", "{{.ID}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                return

            container_ids = stdout.decode().strip().split()
            if not container_ids:
                return

            now = time.time()
            for cid in container_ids:
                # Inspect each container's started timestamp
                inspect_proc = await asyncio.create_subprocess_exec(
                    "docker", "inspect", "--format", "{{.State.StartedAt}}", cid,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                istdout, istderr = await inspect_proc.communicate()
                if inspect_proc.returncode != 0:
                    continue

                started_str = istdout.decode().strip()
                try:
                    t_part = started_str.split(".")[0]
                    if t_part.endswith("Z"):
                        t_part = t_part[:-1]
                    started_dt = datetime.strptime(t_part, "%Y-%m-%dT%H:%M:%S")
                    started_ts = started_dt.replace(tzinfo=timezone.utc).timestamp()
                    age = now - started_ts
                    if age > max_age_seconds:
                        logger.info(f"Reaping container {cid} (age: {age:.1f}s)")
                        kill_proc = await asyncio.create_subprocess_exec("docker", "kill", cid, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                        await kill_proc.wait()
                        rm_proc = await asyncio.create_subprocess_exec("docker", "rm", cid, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                        await rm_proc.wait()
                except Exception as ex:
                    logger.warning(f"Failed to inspect/reap container {cid}: {ex}")

        except Exception as e:
            logger.error(f"Reap failed: {e}")


container_reaper = ContainerReaper()
