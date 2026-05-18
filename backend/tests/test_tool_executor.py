import asyncio
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.tools.tool_executor import execute_tool


class ToolExecutorTests(unittest.TestCase):
    def setUp(self):
        self.prev_cwd = Path.cwd()
        backend_root = Path(__file__).resolve().parents[1]
        os.chdir(backend_root)
        self.workspace_dir = backend_root / "workspace"
        self.workspace_dir.mkdir(exist_ok=True)

    def tearDown(self):
        try:
            target = self.workspace_dir / "executor.txt"
            if target.exists():
                target.unlink()
            if self.workspace_dir.exists() and not any(self.workspace_dir.iterdir()):
                self.workspace_dir.rmdir()
        finally:
            os.chdir(self.prev_cwd)

    def test_write_then_read(self):
        async def _run():
            await execute_tool("write_file", {"path": "executor.txt", "content": "ok"})
            result = await execute_tool("read_file", {"path": "executor.txt"})
            self.assertTrue(result["success"])
            self.assertIn("ok", result["result"])

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
