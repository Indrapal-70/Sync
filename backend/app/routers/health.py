from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.database.redis import redis_client
from app.database.session import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, str]:
    db_status = "ok"
    redis_status = "ok"

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        redis_client.ping()
    except Exception:
        redis_status = "error"

    status = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"

    return {"status": status, "database": db_status, "redis": redis_status}
