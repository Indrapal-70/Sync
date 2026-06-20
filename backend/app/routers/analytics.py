from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.services.metrics_service import metrics_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
router_v1 = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get("/agent-performance")
@router_v1.get("/agent-performance")
async def get_agent_performance(days: int = 7):
    return await metrics_service.get_agent_success_rate(days=days)

@router.get("/healing-summary")
@router_v1.get("/healing-summary")
async def get_healing_summary(days: int = 7):
    return await metrics_service.get_healing_summary(days=days)

@router.get("/task-timeline/{task_id}")
@router_v1.get("/task-timeline/{task_id}")
async def get_task_timeline(task_id: str):
    return await metrics_service.get_task_timeline(task_id)
