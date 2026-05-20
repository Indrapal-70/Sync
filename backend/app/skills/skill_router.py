import asyncio
import time
import httpx
from datetime import datetime

from app.core.config import settings
from app.skills.skill_definitions import SKILLS, get_skill
from app.services.redis_client import publish_event


class SkillRouter:
    """
    Routes agent skill calls to the correct local Ollama model.
    Phase 6: adds retry with exponential backoff + circuit breaker integration.
    Agents call this instead of Ollama directly.
    """

    def __init__(self):
        self.base_url   = settings.ollama_base_url
        # Use the module-level SKILLS dict so in-memory reassignments persist
        self.skills     = SKILLS
        self.call_count = {}
        self.error_count = {}
        self.total_ms   = {}

    # ─────────────────────────────────────────────────────────────────
    # DB persistence helpers (P6-02)
    # ─────────────────────────────────────────────────────────────────

    async def load_assignments_from_db(self, db):
        """Called on startup — loads any saved assignments into memory."""
        from app.models.skill_assignment import SkillAssignment
        rows = db.query(SkillAssignment).all()
        for row in rows:
            if row.skill_name in self.skills:
                self.skills[row.skill_name]["model_key"] = row.model_key
                self.skills[row.skill_name]["model"]     = row.model_name
        print(f"[SkillRouter] Loaded {len(rows)} assignment(s) from DB")

    async def save_assignment_to_db(self, db, skill_name: str, model_key: str, model_name: str):
        """Called after every reassign — upsert into skill_assignments."""
        from app.models.skill_assignment import SkillAssignment
        from sqlalchemy.dialects.postgresql import insert
        from sqlalchemy.sql import func

        stmt = insert(SkillAssignment).values(
            skill_name=skill_name,
            model_key=model_key,
            model_name=model_name,
            updated_by="api",
        ).on_conflict_do_update(
            index_elements=["skill_name"],
            set_={
                "model_key":  model_key,
                "model_name": model_name,
                "updated_at": func.now(),
                "updated_by": "api",
            },
        )
        db.execute(stmt)
        db.commit()

    # ─────────────────────────────────────────────────────────────────
    # P6-06 — Core call path with retry + exponential backoff
    # ─────────────────────────────────────────────────────────────────

    async def call(self, skill_name: str, prompt: str, extra_context: str = "") -> str:
        """
        Route a prompt to the correct model using the named skill.
        Retries with exponential backoff on failure.
        Falls back to FALLBACK_MODEL if all retries exhausted.

        Args:
            skill_name:    one of "plan", "code", "test", "debug", "review"
            prompt:        the main task prompt
            extra_context: optional additional context prepended to prompt

        Returns:
            Raw string response from the model

        Raises:
            ValueError: if skill_name is unknown
            Exception:  if all retries fail and fallback is disabled
        """
        skill          = get_skill(skill_name)
        model          = skill["model"]
        max_retries    = skill.get("max_retries", 1)
        retry_delay    = skill.get("retry_delay_s", 3)
        backoff_factor = skill.get("backoff_factor", 1.5)
        fallback       = skill.get("fallback_on_fail", False)

        system  = skill["system_prompt"]
        full_prompt = system.strip()
        if extra_context:
            full_prompt += f"\n\nCONTEXT:\n{extra_context.strip()}"
        full_prompt += f"\n\nTASK:\n{prompt.strip()}"

        self.call_count[skill_name] = self.call_count.get(skill_name, 0) + 1
        publish_event("skill_called", {
            "skill": skill_name,
            "model": model,
            "timestamp": datetime.utcnow().isoformat(),
        })

        last_error = None

        for attempt in range(max_retries + 1):
            # Wait before retries (not before the first attempt)
            if attempt > 0:
                wait_s = retry_delay * (backoff_factor ** (attempt - 1))
                print(f"[SkillRouter] Retry {attempt}/{max_retries} for skill={skill_name} "
                      f"after {wait_s:.1f}s backoff")
                await asyncio.sleep(wait_s)
                publish_event("skill_retry", {
                    "skill_name": skill_name,
                    "attempt":    attempt,
                    "model":      model,
                    "wait_s":     round(wait_s, 2),
                })

            try:
                start_ms = time.time() * 1000
                result   = await self._call_model(model, skill, full_prompt)
                dur_ms   = int(time.time() * 1000 - start_ms)
                self._record_stats(skill_name, dur_ms, success=True)
                publish_event("skill_completed", {
                    "skill":       skill_name,
                    "model":       model,
                    "duration_ms": dur_ms,
                    "attempt":     attempt,
                })
                print(f"[SkillRouter] skill={skill_name} model={model} "
                      f"duration={dur_ms}ms attempt={attempt}")
                return result

            except Exception as e:
                last_error = e
                self._record_stats(skill_name, 0, success=False)
                publish_event("skill_failed", {
                    "skill_name": skill_name,
                    "model":      model,
                    "error":      str(e),
                    "attempt":    attempt,
                })
                print(f"[SkillRouter] Attempt {attempt} failed: skill={skill_name} error={e}")

        # ── All retries exhausted ──────────────────────────────────
        if fallback and model != settings.fallback_model:
            print(f"[SkillRouter] All retries exhausted for {model}. "
                  f"Falling back to {settings.fallback_model}")
            publish_event("model_fallback_used", {
                "skill_name":    skill_name,
                "failed_model":  model,
                "fallback_model": settings.fallback_model,
                "reason":        str(last_error),
            })
            return await self._call_model(settings.fallback_model, skill, full_prompt)

        raise last_error

    async def _call_model(self, model: str, skill: dict, full_prompt: str) -> str:
        """
        Make a single Ollama API call for the given model.
        Integrates with the circuit breaker (P6-08).
        """
        from app.skills.model_health import get_or_create_cb

        cb = get_or_create_cb(model)
        if not cb.allow_request():
            raise Exception(
                f"Circuit breaker OPEN for {model} — "
                f"rejecting request to protect system stability"
            )

        timeout = skill.get("timeout", 90)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model":  model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": skill.get("temperature", 0.5),
                            "num_predict": 2048,
                        },
                    },
                )
                response.raise_for_status()
                result = response.json().get("response", "")
                cb.record_success()
                return result

        except Exception as e:
            cb.record_failure(model=model)
            raise

    def _record_stats(self, skill_name: str, dur_ms: int, success: bool):
        """Track per-skill performance stats."""
        if not success:
            self.error_count[skill_name] = self.error_count.get(skill_name, 0) + 1
        else:
            self.total_ms[skill_name] = self.total_ms.get(skill_name, 0) + dur_ms

    def get_stats(self) -> dict:
        """Return performance stats for all skills."""
        stats = {}
        for skill_name in self.call_count:
            calls  = self.call_count[skill_name]
            ms     = self.total_ms.get(skill_name, 0)
            errors = self.error_count.get(skill_name, 0)
            stats[skill_name] = {
                "total_calls":  calls,
                "total_errors": errors,
                "avg_ms":       int(ms / calls) if calls > 0 else 0,
                "error_rate":   round(errors / calls, 3) if calls > 0 else 0,
            }
        return stats


skill_router = SkillRouter()
