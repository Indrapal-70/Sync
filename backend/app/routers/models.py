from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
import httpx

from app.database.session import get_db
from app.skills.model_health import check_all_models
from app.skills.skill_definitions import SKILLS, list_skills
from app.skills.skill_router import skill_router
from app.core.config import settings


router = APIRouter(prefix="/api/models", tags=["Models"])


# ─────────────────────────────────────────────────────────────────────────────
# Existing endpoints (Phase 5)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/health")
async def model_health():
    return await check_all_models()


@router.get("/skills")
async def skill_list():
    return list_skills()


@router.get("/stats")
async def skill_stats():
    return skill_router.get_stats()


@router.get("/config")
async def model_config():
    return {
        "thinker_model": settings.thinker_model,
        "builder_model": settings.builder_model,
        "fallback_model": settings.fallback_model,
        "routing": {
            "coder":    settings.builder_model,
            "tester":   settings.builder_model,
            "debugger": settings.thinker_model,
            "reviewer": settings.thinker_model,
            "planner":  settings.thinker_model,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# P6-03 — Skill reassign (now persisted) + assignments list
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/skills/{skill_name}/reassign")
async def reassign_skill(
    skill_name: str,
    body: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Reassign a skill to a different model key ("thinker" or "builder").
    The assignment is persisted to PostgreSQL so it survives restarts.
    """
    if skill_name not in SKILLS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Skill '{skill_name}' not found")

    model_key = body.get("model_key")
    if model_key not in ("thinker", "builder"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="model_key must be 'thinker' or 'builder'",
        )

    # Resolve the actual model name from the key
    new_model = settings.thinker_model if model_key == "thinker" else settings.builder_model

    # Update in-memory SKILLS dict
    SKILLS[skill_name]["model_key"] = model_key
    SKILLS[skill_name]["model"]     = new_model

    # Persist to DB (upsert)
    await skill_router.save_assignment_to_db(db, skill_name, model_key, new_model)

    from app.services.redis_client import publish_event
    publish_event("skill_reassigned", {
        "skill_name": skill_name,
        "model_key":  model_key,
        "model":      new_model,
    })

    return {
        "skill_name": skill_name,
        "model_key":  model_key,
        "model":      new_model,
        "persisted":  True,
    }


@router.get("/assignments")
def get_assignments(db: Session = Depends(get_db)):
    """
    Return all persisted skill assignments from the DB.
    Empty list if no custom assignments have been made yet.
    """
    from app.models.skill_assignment import SkillAssignment
    rows = db.query(SkillAssignment).all()
    return [
        {
            "skill_name": r.skill_name,
            "model_key":  r.model_key,
            "model_name": r.model_name,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            "updated_by": r.updated_by,
        }
        for r in rows
    ]


# ─────────────────────────────────────────────────────────────────────────────
# P6-04 — Model registry (all Ollama models installed)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/registry")
async def model_registry():
    """
    Lists all models installed in Ollama.
    Marks which model is the active thinker and which is the builder.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": str(e), "models": []}

    models = []
    for m in data.get("models", []):
        name = m.get("name", "")
        size_bytes = m.get("size", 0)
        models.append({
            "name":        name,
            "size_gb":     round(size_bytes / 1e9, 2),
            "modified_at": m.get("modified_at"),
            "is_thinker":  name == settings.thinker_model,
            "is_builder":  name == settings.builder_model,
        })

    return {"models": models}


# ─────────────────────────────────────────────────────────────────────────────
# Swap endpoint (Phase 5 — update model key globally)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/swap")
async def swap_models(body: dict = Body(...)):
    """Swap thinker and builder model assignments for all relevant skills."""
    role = body.get("role")  # "thinker" or "builder"
    new_model = body.get("model")

    if not role or not new_model:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Requires 'role' and 'model' fields")

    if role == "thinker":
        settings.thinker_model = new_model
    elif role == "builder":
        settings.builder_model = new_model
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="role must be 'thinker' or 'builder'")

    # Update all skills that use this role
    for skill_name, skill in SKILLS.items():
        if skill["model_key"] == role:
            skill["model"] = new_model

    return {"role": role, "new_model": new_model, "updated_skills": [
        s for s, v in SKILLS.items() if v["model_key"] == role
    ]}
