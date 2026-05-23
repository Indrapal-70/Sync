from collections import defaultdict, deque
from typing import List, Dict
from datetime import datetime
from app.schemas.graph import NodeBlueprint

class GraphExecutor:
    """Converts a NodeBlueprint graph into an ordered list of tasks
       and executes them respecting dependencies."""

    def topological_sort(self, nodes: List[NodeBlueprint]) -> List[NodeBlueprint]:
        """Kahn's algorithm — raises ValueError on cycle detection."""
        node_map = {n.node_id: n for n in nodes}
        in_degree = {n.node_id: 0 for n in nodes}
        graph = defaultdict(list)

        for node in nodes:
            for dep in node.dependencies:
                if dep not in node_map:
                    raise ValueError(
                        f"Node '{node.name}' has unknown dependency: '{dep}'")
                graph[dep].append(node.node_id)
                in_degree[node.node_id] += 1

        queue = deque([n for n in nodes if in_degree[n.node_id] == 0])
        result = []
        while queue:
            current = queue.popleft()
            result.append(current)
            for neighbor_id in graph[current.node_id]:
                in_degree[neighbor_id] -= 1
                if in_degree[neighbor_id] == 0:
                    queue.append(node_map[neighbor_id])

        if len(result) != len(nodes):
            visited = {r.node_id for r in result}
            cycle_nodes = [n.name for n in nodes if n.node_id not in visited]
            raise ValueError(
                f"Cycle detected in graph. Nodes involved: {cycle_nodes}")

        return result

    async def execute_graph(self, workflow_id: str, sorted_nodes: List[NodeBlueprint],
                            db, background_tasks):
        """Creates Task DB rows in execution order and triggers the pipeline."""
        from app.models.task import Task
        from app.services.log_service import create_log
        import uuid

        create_log(db, workflow_id,
            "[GRAPH_EXECUTOR] Starting graph execution mode (planner bypassed)",
            "info")

        tasks_created = []
        for i, node in enumerate(sorted_nodes):
            task = Task(
                id=uuid.uuid4(),
                workflow_id=workflow_id,
                name=node.name,
                description=node.description,
                agent_name=node.agent_hint,
                status="pending",
                node_id=node.node_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                input_data={
                    "expected_output": node.expected_output,
                    "max_retries_override": node.max_retries_override,
                    "dependencies": node.dependencies,
                    "source": "visual_editor",
                    "order": i
                }
            )
            db.add(task)
            tasks_created.append(task)

        db.commit()
        create_log(db, workflow_id,
            f"[GRAPH_EXECUTOR] Created {len(tasks_created)} tasks in dependency order",
            "info")

        # Trigger background execution
        from app.agents.pipeline_orchestrator import run_pipeline
        background_tasks.add_task(
            run_pipeline, workflow_id, db_session=None,
            execution_mode="graph",
            task_order=[str(t.id) for t in tasks_created]
        )

        return tasks_created

graph_executor = GraphExecutor()
