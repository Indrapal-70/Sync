MODEL_MAP = {
    "planner": "kimi-k2.6",
    "coder": "qwen3-coder-next",
    "debugger": "deepseek-v4-pro",
    "reviewer": "deepseek-v4-pro",
    "utility": "minimax-m2.7",
}

FALLBACK_MODEL = "mistral"


def get_model(agent_role: str) -> str:
    """Return the Ollama model name for a given agent role."""
    return MODEL_MAP.get(agent_role, FALLBACK_MODEL)
