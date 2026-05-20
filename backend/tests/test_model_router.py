import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agents.model_router import get_model


class TestModelRouter(unittest.TestCase):

    def test_known_roles(self):
        self.assertEqual(get_model("planner"),  "mistral:latest")
        self.assertEqual(get_model("coder"),    "deepseek-coder:6.7b")
        self.assertEqual(get_model("tester"),   "deepseek-coder:6.7b")
        self.assertEqual(get_model("debugger"), "mistral:latest")
        self.assertEqual(get_model("reviewer"), "mistral:latest")

    def test_fallback(self):
        self.assertEqual(get_model("unknown"), "mistral:latest")
        self.assertEqual(get_model(""),        "mistral:latest")


if __name__ == "__main__":
    unittest.main()