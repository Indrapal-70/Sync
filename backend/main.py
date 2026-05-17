from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.session import init_db
from app.services.event_broadcaster import start_broadcaster
from app.routers import health, workflows, tasks, logs, websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[SYNC] Starting up...")
    init_db()
    print("[SYNC] Database tables verified")
    asyncio.create_task(start_broadcaster())
    print("[SYNC] Redis broadcaster started")
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


@app.get("/")
async def root():
    return {
        "platform": "SYNC",
        "status": "operational",
        "version": "0.3.0",
        "docs": "/docs",
    }
