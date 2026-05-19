from fastapi import APIRouter

from app.skills.model_health import check_all_models
from app.skills.skill_definitions import list_skills
from app.skills.skill_router import skill_router
from app.core.config import settings


router = APIRouter(prefix="/api/models", tags=["Models"])


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
            "coder": settings.builder_model,
            "tester": settings.builder_model,
            "debugger": settings.thinker_model,
            "reviewer": settings.thinker_model,
            "planner": settings.thinker_model
        }
    }
