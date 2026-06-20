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
from app.routers import health, workflows, tasks, logs, websocket_router, system, analytics
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

    # Start background broadcaster
    broadcaster_task = asyncio.create_task(start_broadcaster())
    app.state.background_tasks = {broadcaster_task}
    broadcaster_task.add_done_callback(app.state.background_tasks.discard)
    print("[SYNC] Redis broadcaster started")

    # Start queued pipeline workers
    from app.core.config import MAX_CONCURRENT_PIPELINES
    from app.services.pipeline_worker import PipelineWorker
    workers = [PipelineWorker(i) for i in range(MAX_CONCURRENT_PIPELINES)]
    worker_tasks = [asyncio.create_task(w.run_forever()) for w in workers]
    for task in worker_tasks:
        app.state.background_tasks.add(task)
        task.add_done_callback(app.state.background_tasks.discard)

    skills = list_skills()
    print(f"[SYNC] {len(skills)} skills loaded: {[s['name'] for s in skills]}")
    yield
    # ── Shutdown ─────────────────────────────────────────────────────
    print("[SYNC] Shutting down...")
    for w in workers:
        w.stop()
    # Cancel and gather all background tasks
    tasks_to_cancel = list(app.state.background_tasks)
    for task in tasks_to_cancel:
        task.cancel()
    await asyncio.gather(*tasks_to_cancel, return_exceptions=True)


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
app.include_router(templates.router_v1)
app.include_router(analytics.router)
app.include_router(analytics.router_v1)
app.include_router(system.router)


@app.get("/")
async def root():
    return {
        "platform": "SYNC",
        "status": "operational",
        "version": "0.6.0",
        "docs": "/docs",
    }
