import httpx
import time

from app.core.config import settings


REQUIRED_MODELS = [
    settings.thinker_model,
    settings.builder_model,
]


async def check_model_available(model_name: str) -> dict:
    """
    Send a minimal test prompt to verify a model responds.
    Uses keep_alive=0 to unload model immediately after check,
    freeing RAM for the next model.
    """
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "hi",
                    "stream": False,
                    "keep_alive": 0,
                    "options": {"num_predict": 3},
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
    Check each model SEQUENTIALLY (not parallel) to avoid
    loading both into RAM at the same time.
    16GB RAM cannot hold both models simultaneously.
    """
    results = []

    for model_name in REQUIRED_MODELS:
        print(f"[ModelHealth] Checking {model_name}...")
        result = await check_model_available(model_name)
        status = "OK" if result["available"] else "UNAVAILABLE"
        print(f"[ModelHealth] {model_name}: {status} ({result['response_ms']}ms)")
        if not result["available"]:
            print(f"[ModelHealth] Error: {result['error']}")
        results.append(result)

    all_ok = all(r["available"] for r in results)

    report = {
        "all_models_ok": all_ok,
        "models": {r["model"]: r for r in results},
    }

    if not all_ok:
        unavailable = [r["model"] for r in results if not r["available"]]
        print(f"[ModelHealth] WARNING: Unavailable models: {unavailable}")
        print(f"[ModelHealth] Fallback active: {settings.fallback_model}")
    else:
        print("[ModelHealth] All models OK — pipeline ready")

    return report


_last_health_report: dict = {}


async def run_startup_check() -> dict:
    global _last_health_report
    _last_health_report = await check_all_models()
    return _last_health_report


def get_last_health_report() -> dict:
    return _last_health_report