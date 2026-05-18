import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agents.model_router import get_model


class ModelRouterTests(unittest.TestCase):
    def test_model_mapping(self):
        self.assertEqual(get_model("planner"), "kimi-k2.6:cloud")
        self.assertEqual(get_model("coder"), "qwen3-coder-next")
        self.assertEqual(get_model("debugger"), "deepseek-v4-pro:cloud")
        self.assertEqual(get_model("reviewer"), "deepseek-v4-pro:cloud")
        self.assertEqual(get_model("utility"), "minimax-m2.7:cloud")

    def test_model_fallback(self):
        self.assertEqual(get_model("unknown"), "mistral")


if __name__ == "__main__":
    unittest.main()
