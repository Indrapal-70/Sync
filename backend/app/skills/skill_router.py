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
    Agents call this instead of Ollama directly.
    """

    def __init__(self):
        self.base_url = settings.ollama_base_url
        # Use the module-level SKILLS dict directly so reassignments persist in-memory
        self.skills = SKILLS
        self.call_count = {}
        self.error_count = {}
        self.total_ms = {}

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
    # Core call path
    # ─────────────────────────────────────────────────────────────────

    async def call(self, skill_name: str, prompt: str, extra_context: str = "") -> str:
        """
        Route a prompt to the correct model using the named skill.

        Args:
            skill_name: one of "plan", "code", "test", "debug", "review"
            prompt: the main task prompt
            extra_context: optional additional context prepended to prompt

        Returns:
            Raw string response from the model

        Raises:
            ValueError: if skill_name is unknown
            httpx.TimeoutException: if model takes too long
            Exception: on Ollama connection failure
        """
        skill = get_skill(skill_name)
        model = skill["model"]
        system = skill["system_prompt"]
        timeout = skill["timeout"]

        full_prompt = system.strip()
        if extra_context:
            full_prompt += f"\n\nCONTEXT:\n{extra_context.strip()}"
        full_prompt += f"\n\nTASK:\n{prompt.strip()}"

        start = datetime.utcnow()
        self.call_count[skill_name] = self.call_count.get(skill_name, 0) + 1

        publish_event(
            "skill_called",
            {"skill": skill_name, "model": model, "timestamp": start.isoformat()},
        )

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": skill["temperature"],
                            "num_predict": 2048,
                        },
                    },
                )
                response.raise_for_status()
                result = response.json().get("response", "")

                duration_ms = int(
                    (datetime.utcnow() - start).total_seconds() * 1000
                )
                self.total_ms[skill_name] = (
                    self.total_ms.get(skill_name, 0) + duration_ms
                )

                print(
                    f"[SkillRouter] skill={skill_name} "
                    f"model={model} duration={duration_ms}ms"
                )
                publish_event(
                    "skill_completed",
                    {
                        "skill": skill_name,
                        "model": model,
                        "duration_ms": duration_ms,
                    },
                )
                return result

        except httpx.TimeoutException:
            publish_event(
                "skill_failed",
                {"skill": skill_name, "model": model, "error": "timeout"},
            )
            self.error_count[skill_name] = (
                self.error_count.get(skill_name, 0) + 1
            )
            if model != settings.fallback_model:
                print(
                    f"[SkillRouter] {model} timed out for skill={skill_name}. "
                    f"Trying fallback: {settings.fallback_model}"
                )
                return await self._fallback_call(
                    settings.fallback_model, full_prompt, timeout
                )
            raise

        except Exception as e:
            publish_event(
                "skill_failed",
                {"skill": skill_name, "model": model, "error": str(e)},
            )
            self.error_count[skill_name] = (
                self.error_count.get(skill_name, 0) + 1
            )
            print(f"[SkillRouter] Error: skill={skill_name} error={e}")
            raise

    async def _fallback_call(self, model: str, full_prompt: str, timeout: int) -> str:
        """Call the fallback model directly when primary fails."""
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": 0.5, "num_predict": 2048},
                },
            )
            response.raise_for_status()
            return response.json().get("response", "")

    def get_stats(self) -> dict:
        """Return performance stats for all skills."""
        stats = {}
        for skill_name in self.call_count:
            calls = self.call_count[skill_name]
            ms = self.total_ms.get(skill_name, 0)
            errors = self.error_count.get(skill_name, 0)
            stats[skill_name] = {
                "total_calls": calls,
                "total_errors": errors,
                "avg_ms": int(ms / calls) if calls > 0 else 0,
                "error_rate": round(errors / calls, 3) if calls > 0 else 0,
            }
        return stats


skill_router = SkillRouter()
