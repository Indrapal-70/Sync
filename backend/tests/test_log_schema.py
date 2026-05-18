import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.log import LogCreate


class LogSchemaTests(unittest.TestCase):
    def test_log_create_accepts_agent_metadata(self):
        log = LogCreate(
            workflow_id="00000000-0000-0000-0000-000000000000",
            message="test",
            agent_name="coder",
            pipeline_stage="coding",
        )
        self.assertEqual(log.agent_name, "coder")
        self.assertEqual(log.pipeline_stage, "coding")


if __name__ == "__main__":
    unittest.main()
