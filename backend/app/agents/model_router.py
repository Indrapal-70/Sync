MODEL_MAP = {
    "planner":  "mistral:latest",
    "coder":    "deepseek-coder:6.7b",
    "tester":   "deepseek-coder:6.7b",
    "debugger": "mistral:latest",
    "reviewer": "mistral:latest",
    "utility":  "mistral:latest",
}

FALLBACK_MODEL = "mistral:latest"


def get_model(agent_role: str) -> str:
    """Return the Ollama model name for a given agent role."""
    return MODEL_MAP.get(agent_role, FALLBACK_MODEL)