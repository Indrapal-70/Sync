import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.session import init_db
from app.skills.model_health import run_startup_check
from app.skills.skill_definitions import list_skills
from app.services.event_broadcaster import start_broadcaster
from app.routers import health, workflows, tasks, logs, websocket_router
from app.routers import models as models_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[SYNC] Starting Phase 5 - Two-Model Skill Router")
    init_db()
    print("[SYNC] Database ready")

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
    # Shutdown
    print("[SYNC] Shutting down...")


app = FastAPI(
    title="SYNC Orchestration Platform",
    description="Real-time multi-agent workflow orchestration",
    version="0.3.0",
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


@app.get("/")
async def root():
    return {
        "platform": "SYNC",
        "status": "operational",
        "version": "0.3.0",
        "docs": "/docs",
    }
