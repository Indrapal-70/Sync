import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.session import init_db, SessionLocal
from app.skills.model_health import run_startup_check
from app.skills.skill_definitions import list_skills
from app.skills.skill_router import skill_router
from app.services.event_broadcaster import start_broadcaster
from app.routers import health, workflows, tasks, logs, websocket_router
from app.routers import models as models_router

logger = logging.getLogger("sync")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────
    print("[SYNC] Starting Phase 6 - Skill Persistence + Resilience")
    init_db()
    print("[SYNC] Database ready")

    # P6-02: Load persisted skill assignments from DB
    db = SessionLocal()
    try:
        await skill_router.load_assignments_from_db(db)
        logger.info("[STARTUP] Skill assignments loaded from DB")
    finally:
        db.close()

    health_report = await run_startup_check()
    if health_report["all_models_ok"]:
        print("[SYNC] Both models healthy - pipeline ready")
    else:
        print("[SYNC] WARNING: Some models unavailable - fallback active")

    asyncio.create_task(start_broadcaster())
    print("[SYNC] Redis broadcaster started")

    skills = list_skills()
    print(f"[SYNC] {len(skills)} skills loaded: {[s['name'] for s in skills]}")
    yield
    # ── Shutdown ─────────────────────────────────────────────────────
    print("[SYNC] Shutting down...")


app = FastAPI(
    title="SYNC Orchestration Platform",
    description="Real-time multi-agent workflow orchestration",
    version="0.6.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(workflows.router)
app.include_router(tasks.router)
app.include_router(logs.router)
app.include_router(websocket_router.router)
app.include_router(models_router.router)
from app.routers import templates
app.include_router(templates.router)


@app.get("/")
async def root():
    return {
        "platform": "SYNC",
        "status": "operational",
        "version": "0.6.0",
        "docs": "/docs",
    }
