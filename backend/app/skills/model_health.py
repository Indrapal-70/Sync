import httpx
import time
from enum import Enum

from app.core.config import settings
from app.services.redis_client import publish_event


# ─────────────────────────────────────────────────────────────────────────────
# P6-08 — Circuit Breaker
# ─────────────────────────────────────────────────────────────────────────────

class CBState(Enum):
    CLOSED    = "closed"     # Normal operation — requests pass through
    OPEN      = "open"       # Failing — reject all calls immediately
    HALF_OPEN = "half_open"  # Recovery probe — allow one test request


class CircuitBreaker:
    """
    Per-model circuit breaker that auto-recovers after a timeout.

    State machine:
      CLOSED  --(fail_count >= threshold)--> OPEN
      OPEN    --(timeout_s elapsed)---------> HALF_OPEN
      HALF_OPEN --(success)----------------> CLOSED
      HALF_OPEN --(failure)----------------> OPEN
    """

    def __init__(self, threshold: int = 3, timeout_s: int = 120):
        self.threshold  = threshold   # consecutive failures before OPEN
        self.timeout_s  = timeout_s   # seconds to wait before HALF_OPEN probe
        self.state      = CBState.CLOSED
        self.fail_count = 0
        self.opened_at  = None

    def record_success(self):
        self.fail_count = 0
        if self.state != CBState.CLOSED:
            print(f"[CircuitBreaker] Recovered → CLOSED")
        self.state = CBState.CLOSED

    def record_failure(self, model: str = "unknown"):
        self.fail_count += 1
        if self.state == CBState.HALF_OPEN or self.fail_count >= self.threshold:
            self.state     = CBState.OPEN
            self.opened_at = time.time()
            print(f"[CircuitBreaker] {model} → OPEN (fail_count={self.fail_count})")
            publish_event("circuit_breaker_opened", {
                "model":      model,
                "fail_count": self.fail_count,
                "threshold":  self.threshold,
            })

    def allow_request(self) -> bool:
        if self.state == CBState.CLOSED:
            return True
        if self.state == CBState.OPEN:
            elapsed = time.time() - (self.opened_at or 0)
            if elapsed >= self.timeout_s:
                self.state = CBState.HALF_OPEN
                print(f"[CircuitBreaker] Probe allowed → HALF_OPEN")
                return True  # Allow one probe request
            return False
        # HALF_OPEN: allow the one probe
        return True

    @property
    def status(self) -> str:
        return self.state.value


# One CircuitBreaker instance per model — keyed by model name
_cb_threshold = getattr(settings, "circuit_breaker_threshold", 3)
_cb_timeout   = getattr(settings, "circuit_breaker_timeout_s", 120)

circuit_breakers: dict[str, CircuitBreaker] = {
    settings.thinker_model: CircuitBreaker(_cb_threshold, _cb_timeout),
    settings.builder_model: CircuitBreaker(_cb_threshold, _cb_timeout),
    settings.fallback_model: CircuitBreaker(_cb_threshold, _cb_timeout),
}


def get_or_create_cb(model: str) -> CircuitBreaker:
    """Get existing circuit breaker or create one for a new model name."""
    if model not in circuit_breakers:
        circuit_breakers[model] = CircuitBreaker(_cb_threshold, _cb_timeout)
    return circuit_breakers[model]


# ─────────────────────────────────────────────────────────────────────────────
# Model health checker (unchanged from Phase 5, enhanced with CB status)
# ─────────────────────────────────────────────────────────────────────────────

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

        # P6-08: include circuit breaker state in health report
        cb = get_or_create_cb(model_name)
        result["circuit_breaker"] = cb.status

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