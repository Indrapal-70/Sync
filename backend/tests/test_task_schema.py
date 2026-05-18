import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.task import TaskUpdate


class TaskSchemaTests(unittest.TestCase):
    def test_task_update_accepts_pipeline_fields(self):
        update = TaskUpdate(
            status="running",
            current_agent="coder",
            pipeline_stage="coding",
            retry_count=1,
            agent_output={"coder": {"success": True}},
        )
        self.assertEqual(update.status, "running")
        self.assertEqual(update.current_agent, "coder")
        self.assertEqual(update.pipeline_stage, "coding")
        self.assertEqual(update.retry_count, 1)
        self.assertIn("coder", update.agent_output)


if __name__ == "__main__":
    unittest.main()
