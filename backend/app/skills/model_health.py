import httpx

from app.core.config import settings


REQUIRED_MODELS = [
    settings.thinker_model,
    settings.builder_model,
]


async def check_model_available(model_name: str) -> dict:
    """
    Send a minimal test prompt to verify a model is loaded and responds.
    Returns dict with keys: model, available, response_ms, error
    """
    import time

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "Reply with the single word: ready",
                    "stream": False,
                    "options": {"num_predict": 5},
                },
            )
            response.raise_for_status()
            elapsed_ms = int((time.time() - start) * 1000)
            return {
                "model": model_name,
                "available": True,
                "response_ms": elapsed_ms,
                "error": None,
            }
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            "model": model_name,
            "available": False,
            "response_ms": elapsed_ms,
            "error": str(e),
        }


async def check_all_models() -> dict:
    """
    Check all required models. Returns full health report.
    Called on FastAPI startup.
    """
    import asyncio

    results = await asyncio.gather(
        *[check_model_available(m) for m in REQUIRED_MODELS]
    )
    all_ok = all(r["available"] for r in results)

    report = {
        "all_models_ok": all_ok,
        "models": {r["model"]: r for r in results},
    }

    for r in results:
        status = "OK" if r["available"] else "UNAVAILABLE"
        print(f"[ModelHealth] {r['model']}: {status} ({r['response_ms']}ms)")

    if not all_ok:
        unavailable = [r["model"] for r in results if not r["available"]]
        print(
            "[ModelHealth] WARNING: These models are unavailable: "
            f"{unavailable}"
        )
        print(f"[ModelHealth] Fallback model: {settings.fallback_model}")
        print("[ModelHealth] Pipeline will use fallback for unavailable models.")

    return report


_last_health_report: dict = {}


async def run_startup_check() -> dict:
    global _last_health_report
    _last_health_report = await check_all_models()
    return _last_health_report


def get_last_health_report() -> dict:
    return _last_health_report
