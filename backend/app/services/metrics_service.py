from datetime import datetime, timedelta
from app.database.session import SessionLocal
from app.models.healing_event import HealingEvent
from app.models.agent_metric import AgentMetric
from sqlalchemy import func, desc

class MetricsService:
    async def record_agent_run(
        self, task_id: str, agent_name: str, step: int,
        status: str, duration_ms: float, healing_cycle: int = 0,
    ) -> None:
        db = SessionLocal()
        try:
            metric = AgentMetric(
                task_id=str(task_id),
                agent_name=agent_name,
                step=step,
                status=status,
                duration_ms=duration_ms,
                healing_cycle=healing_cycle
            )
            db.add(metric)
            db.commit()
        finally:
            db.close()

    async def record_healing_event(
        self, task_id: str, cycle: int, failed_agent: str,
        error_summary: str, injected_node_ids: list[str],
    ) -> str:
        db = SessionLocal()
        try:
            truncated_summary = error_summary[:500] if error_summary else None
            event = HealingEvent(
                task_id=str(task_id),
                cycle=cycle,
                failed_agent=failed_agent,
                error_summary=truncated_summary,
                injected_node_ids=injected_node_ids,
                resolved=False
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            return str(event.id)
        finally:
            db.close()

    async def mark_healing_resolved(self, task_id: str, cycle: int) -> None:
        db = SessionLocal()
        try:
            event = db.query(HealingEvent).filter(
                HealingEvent.task_id == str(task_id),
                HealingEvent.cycle == cycle
            ).first()
            if event:
                event.resolved = True
                event.resolved_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()

    async def get_agent_success_rate(self, agent_name: str | None = None, days: int = 7) -> dict | list[dict]:
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            if agent_name:
                query = db.query(AgentMetric).filter(
                    AgentMetric.agent_name == agent_name,
                    AgentMetric.created_at >= cutoff
                )
                metrics = query.all()
                total = len(metrics)
                passed = len([m for m in metrics if m.status == 'passed'])
                failed = len([m for m in metrics if m.status == 'failed'])
                rate = passed / total if total > 0 else 0.0
                return {
                    "agent_name": agent_name,
                    "total_runs": total,
                    "passed": passed,
                    "failed": failed,
                    "success_rate": rate
                }
            else:
                from sqlalchemy import distinct
                agents = [r[0] for r in db.query(distinct(AgentMetric.agent_name)).all()]
                results = []
                for name in agents:
                    agent_metrics = db.query(AgentMetric).filter(
                        AgentMetric.agent_name == name,
                        AgentMetric.created_at >= cutoff
                    ).all()
                    total = len(agent_metrics)
                    passed = len([m for m in agent_metrics if m.status == 'passed'])
                    failed = len([m for m in agent_metrics if m.status == 'failed'])
                    rate = passed / total if total > 0 else 0.0
                    results.append({
                        "agent_name": name,
                        "total_runs": total,
                        "passed": passed,
                        "failed": failed,
                        "success_rate": rate
                    })
                return results
        finally:
            db.close()

    async def get_healing_summary(self, days: int = 7) -> dict:
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            events = db.query(HealingEvent).filter(HealingEvent.created_at >= cutoff).all()
            
            total_cycles = len(events)
            resolved = len([e for e in events if e.resolved])
            unresolved = total_cycles - resolved
            
            distinct_tasks = len(set(e.task_id for e in events))
            avg_cycles = total_cycles / distinct_tasks if distinct_tasks > 0 else 0.0
            
            agent_counts = {}
            for e in events:
                agent_counts[e.failed_agent] = agent_counts.get(e.failed_agent, 0) + 1
            most_common = max(agent_counts, key=agent_counts.get) if agent_counts else ""
            
            return {
                "total_healing_cycles": total_cycles,
                "resolved": resolved,
                "unresolved": unresolved,
                "avg_cycles_per_task": avg_cycles,
                "most_common_failed_agent": most_common
            }
        finally:
            db.close()

    async def get_task_timeline(self, task_id: str) -> list[dict]:
        db = SessionLocal()
        try:
            metrics = db.query(AgentMetric).filter(
                AgentMetric.task_id == str(task_id)
            ).order_by(AgentMetric.created_at.asc()).all()
            
            return [
                {
                    "id": str(m.id),
                    "task_id": m.task_id,
                    "agent_name": m.agent_name,
                    "step": m.step,
                    "status": m.status,
                    "duration_ms": m.duration_ms,
                    "healing_cycle": m.healing_cycle,
                    "created_at": m.created_at
                }
                for m in metrics
            ]
        finally:
            db.close()

metrics_service = MetricsService()
