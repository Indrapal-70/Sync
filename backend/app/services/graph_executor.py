from collections import defaultdict, deque
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import asyncio
import logging
import copy
from uuid import UUID

from app.schemas.graph import NodeBlueprint
from app.models.task import Task
from app.agents.base_agent import get_agent_for_type
from app.services.redis_client import publish_event
from app.services.log_service import create_log
from app.services.context_buffer import agent_context_buffer

logger = logging.getLogger("sync.graph_executor")

class GraphExecutor:
    """Converts a NodeBlueprint graph into an ordered list of tasks
       and executes them respecting dependencies with support for healing loops."""

    def __init__(self):
        self.active_graphs = {}
        self.healing_logs = {}

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
                            db, background_tasks, raw_graph: dict = None):
        """Creates Task DB rows in execution order and triggers the pipeline."""
        create_log(db, workflow_id,
            "[GRAPH_EXECUTOR] Starting graph execution mode (planner bypassed)",
            "info")

        # Save active graph representation (React Flow nodes/edges) in-memory
        if raw_graph and raw_graph.get("nodes"):
            self.active_graphs[workflow_id] = raw_graph
        else:
            # Reconstruct basic nodes and edges representation
            nodes_list = []
            edges_list = []
            for node in sorted_nodes:
                nodes_list.append({
                    "id": node.node_id,
                    "type": "agentNode",
                    "data": {
                        "label": node.name,
                        "agentType": node.agent_hint,
                        "taskName": node.name,
                        "taskDescription": node.description,
                        "expectedOutput": node.expected_output,
                    },
                    "position": {"x": 100, "y": 100}
                })
                for dep in node.dependencies:
                    edges_list.append({
                        "id": f"edge_{dep}_{node.node_id}",
                        "source": dep,
                        "target": node.node_id
                    })
            self.active_graphs[workflow_id] = {
                "nodes": nodes_list,
                "edges": edges_list
            }

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
        from app.services.execution_queue import execution_queue
        payload = {
            "task_id": workflow_id,
            "mode": "graph",
            "args": {
                "workflow_id": workflow_id
            }
        }
        pos = await execution_queue.enqueue(workflow_id, payload)

        return tasks_created, pos

    async def run_graph(self, workflow_id: str, db):
        """Execute a graph dynamically using custom DAG running engine with auto-healing loops."""
        graph = self.active_graphs.get(str(workflow_id))
        if not graph:
            logger.warning(f"Graph layout not found for workflow {workflow_id}. Falling back to default.")
            return

        tasks = db.query(Task).filter(Task.workflow_id == workflow_id).all()
        node_to_task = {t.node_id: str(t.id) for t in tasks if t.node_id}

        # Initialize node states
        node_states = {}
        for node in graph["nodes"]:
            node_id = node["id"]
            if node.get("type") == "startNode" or node_id == "start":
                node_states[node_id] = "done"
            else:
                node_states[node_id] = "pending"

        healing_cycles = {}  # maps task_id to int

        while True:
            # Find eligible pending nodes
            eligible_nodes = []
            for node in graph["nodes"]:
                node_id = node["id"]
                if node_states.get(node_id) != "pending":
                    continue

                if node.get("type") == "startNode" or node_id == "start":
                    continue

                if node.get("type") == "endNode" or node_id == "end":
                    # End node is eligible when all predecessors are done
                    preds = [edge["source"] for edge in graph["edges"] if edge["target"] == node_id]
                    if preds and all(node_states.get(p) == "done" for p in preds):
                        node_states[node_id] = "done"
                    continue

                preds = [edge["source"] for edge in graph["edges"] if edge["target"] == node_id]
                agent_type = node.get("data", {}).get("agentType")

                if agent_type == "debugger" or node.get("type") == "DebuggerAgent":
                    # Debugger runs if its predecessor (Tester) is failed
                    if preds and any(node_states.get(p) == "failed" for p in preds) and all(node_states.get(p) in ["done", "failed"] for p in preds):
                        eligible_nodes.append(node)
                else:
                    # Other nodes run when all predecessors are done
                    if not preds or all(node_states.get(p) == "done" for p in preds):
                        eligible_nodes.append(node)

            if not eligible_nodes:
                # Execution finished or blocked
                break

            # Process eligible nodes sequentially
            for node in eligible_nodes:
                node_id = node["id"]
                node_states[node_id] = "running"
                
                task_id = node_to_task.get(node_id)
                if not task_id:
                    # Create injected node Task
                    task_id = str(uuid.uuid4())
                    task = Task(
                        id=UUID(task_id),
                        workflow_id=UUID(workflow_id),
                        name=node["data"].get("label") or "Injected Debugger",
                        description="Injected Debugger Task",
                        agent_name="debugger",
                        status="running",
                        node_id=node_id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        input_data={
                            "error_context": node["data"].get("error_context"),
                            "source": "healing"
                        }
                    )
                    db.add(task)
                    db.commit()
                    node_to_task[node_id] = task_id
                else:
                    task = db.query(Task).filter_by(id=task_id).first()
                    task.status = "running"
                    task.updated_at = datetime.utcnow()
                    db.commit()

                publish_event("task_updated", {
                    "id": str(task_id),
                    "status": "running",
                    "agent_name": task.agent_name
                })

                # Resolve predecessor inputs
                pred_ids = [edge["source"] for edge in graph["edges"] if edge["target"] == node_id]
                predecessor_outputs = {}
                for p_id in pred_ids:
                    pt_id = node_to_task.get(p_id)
                    if pt_id:
                        pt = db.query(Task).filter_by(id=pt_id).first()
                        if pt and pt.agent_output:
                            predecessor_outputs[p_id] = pt.agent_output

                # Extract code/explanation from predecessors
                code = ""
                explanation = ""
                for out in predecessor_outputs.values():
                    if isinstance(out, dict):
                        if "output" in out and isinstance(out["output"], dict):
                            code = out["output"].get("code", code)
                            explanation = out["output"].get("explanation", explanation)
                        if "fixed_code" in out:
                            code = out["fixed_code"]
                        if "output" in out and isinstance(out["output"], dict) and "fixed_code" in out["output"]:
                            code = out["output"].get("fixed_code", code)

                context = {
                    "name": task.name,
                    "description": task.description,
                    "input_data": task.input_data or {},
                    "previous_error": task.input_data.get("error_context", {}).get("sandbox_result", {}).get("stderr") if task.input_data else None,
                    "code_output": {"code": code, "explanation": explanation},
                    "test_results": {},
                    "task_id": str(task_id),
                    "workflow_id": str(workflow_id),
                    "db": db
                }

                if task.agent_name == "debugger":
                    for out in predecessor_outputs.values():
                        if isinstance(out, dict) and out.get("agent") == "tester":
                            context["test_results"] = out
                    if not context.get("test_results") and task.input_data and "error_context" in task.input_data:
                        err_ctx = task.input_data["error_context"]
                        context["test_results"] = {
                            "results": {
                                "critical_issues": [err_ctx.get("error") or "Test failed in sandbox"],
                                "stdout": err_ctx.get("stdout"),
                                "stderr": err_ctx.get("stderr"),
                            }
                        }

                try:
                    import time
                    from app.services.metrics_service import metrics_service
                    
                    agent_cls = get_agent_for_type(task.agent_name)
                    agent_inst = agent_cls(db, workflow_id, task_id)
                    
                    start_time = time.time()
                    result = await agent_inst.run(context)
                    duration_ms = (time.time() - start_time) * 1000.0
                    
                    # Record run metric
                    entries = agent_context_buffer._store.get(str(task_id), [])
                    if entries:
                        last_entry = entries[-1]
                        await metrics_service.record_agent_run(
                            task_id=str(task_id),
                            agent_name=last_entry.agent_name,
                            step=last_entry.step,
                            status=last_entry.status,
                            duration_ms=duration_ms,
                            healing_cycle=last_entry.healing_cycle
                        )

                    # Determine pass/fail status
                    status_str = result.get("status")
                    if not status_str:
                        if result.get("success"):
                            status_str = "passed" if result.get("all_passed", True) is not False else "failed"
                        else:
                            status_str = "failed"

                    task.status = "done" if status_str == "passed" else "failed"
                    task.agent_output = result
                    db.commit()

                    publish_event("task_updated", {
                        "id": str(task_id),
                        "status": task.status,
                        "agent_name": task.agent_name
                    })

                    node_states[node_id] = "done" if status_str == "passed" else "failed"

                    if status_str == "passed":
                        self.reset_descendants(graph, node_states, node_to_task, node_id, db)
                        if str(task_id) in self.healing_logs:
                            for entry in self.healing_logs[str(task_id)]:
                                entry["resolved"] = True
                                await metrics_service.mark_healing_resolved(str(task_id), entry["cycle"])
                        await agent_context_buffer.clear(task_id)
                    else:
                        # Auto-healing sequence
                        cycles = healing_cycles.get(task_id, 0)
                        if cycles >= 3:
                            logger.error(f"Max healing cycles reached for task {task_id}")
                            node_states[node_id] = "failed"
                            await agent_context_buffer.clear(task_id)
                            break
                        else:
                            healing_cycles[task_id] = cycles + 1
                            # Broadcast healing_started
                            publish_event("healing_started", {
                                "task_id": str(task_id),
                                "cycle": cycles + 1,
                                "failed_agent": task.agent_name
                            })
                            # Patch the graph
                            patched_graph = await self._inject_healing_nodes(
                                graph=graph,
                                failed_node_id=node_id,
                                error_context=result,
                                task_id=task_id,
                                cycle_number=cycles + 1
                            )
                            graph = patched_graph
                            self.active_graphs[str(workflow_id)] = patched_graph

                            # Record healing event in metrics DB
                            injected_node_ids = []
                            for n in patched_graph["nodes"]:
                                if n["data"].get("spawned_by_healing") and n["data"].get("cycle") == cycles + 1:
                                    injected_node_ids.append(n["id"])
                            error_summary = str(result.get("error") or result.get("stderr") or "Unknown error")
                            
                            await metrics_service.record_healing_event(
                                task_id=str(task_id),
                                cycle=cycles + 1,
                                failed_agent=task.agent_name,
                                error_summary=error_summary,
                                injected_node_ids=injected_node_ids
                            )

                            # Broadcast graph_patched
                            publish_event("graph_patched", {
                                "task_id": str(task_id),
                                "graph": patched_graph,
                                "healing_cycle": cycles + 1
                            })

                            # Find injected debugger and reset to pending
                            debugger_node = None
                            for n in patched_graph["nodes"]:
                                if n["data"].get("spawned_by_healing") and n["data"].get("cycle") == cycles + 1:
                                    debugger_node = n
                                    break
                            
                            # Append to healing_logs dict
                            h_logs = self.healing_logs.setdefault(str(task_id), [])
                            h_logs.append({
                                "cycle": cycles + 1,
                                "failed_agent": task.agent_name,
                                "injected_nodes": [debugger_node["id"]] if debugger_node else [],
                                "resolved": False
                            })
                            
                            if debugger_node:
                                node_states[debugger_node["id"]] = "pending"
                                
                            # Reset predecessor Coder to pending
                            coder_node_id = None
                            for edge in patched_graph["edges"]:
                                if debugger_node and edge["source"] == debugger_node["id"]:
                                    coder_node_id = edge["target"]
                                    break
                            if coder_node_id:
                                node_states[coder_node_id] = "pending"
                                coder_task_id = node_to_task.get(coder_node_id)
                                if coder_task_id:
                                    coder_task = db.query(Task).filter_by(id=coder_task_id).first()
                                    if coder_task:
                                        coder_task.status = "pending"
                                        db.commit()
                                        publish_event("task_updated", {
                                            "id": str(coder_task_id),
                                            "status": "pending"
                                        })

                except Exception as e:
                    logger.error(f"Failed to run agent in graph mode: {e}")
                    task.status = "failed"
                    db.commit()
                    publish_event("task_updated", {
                        "id": str(task_id),
                        "status": "failed"
                    })
                    node_states[node_id] = "failed"
                    await agent_context_buffer.clear(task_id)
                    break

    def reset_descendants(self, graph, node_states, node_to_task, node_id, db):
        queue = [node_id]
        visited = set()
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            for edge in graph["edges"]:
                if edge["source"] == curr:
                    tgt = edge["target"]
                    if tgt not in visited:
                        if node_states.get(tgt) in ["done", "failed"]:
                            tgt_node = next((n for n in graph["nodes"] if n["id"] == tgt), None)
                            is_dbg = tgt_node and (tgt_node.get("type") == "DebuggerAgent" or tgt_node.get("data", {}).get("agentType") == "debugger")
                            if not is_dbg:
                                node_states[tgt] = "pending"
                                t_id = node_to_task.get(tgt)
                                if t_id:
                                    task = db.query(Task).filter_by(id=t_id).first()
                                    if task:
                                        task.status = "pending"
                                        db.commit()
                                        publish_event("task_updated", {
                                            "id": str(t_id),
                                            "status": "pending"
                                        })
                        queue.append(tgt)

    async def _inject_healing_nodes(
        self,
        graph: dict,
        failed_node_id: str,
        error_context: dict,
        task_id: str,
        cycle_number: int,
    ) -> dict:
        """Inject DebuggerAgent and loop back retry edges to the predecessor CoderAgent."""
        # 1. Clone graph
        new_graph = copy.deepcopy(graph)

        # 2. Find failed node
        failed_node = None
        for node in new_graph["nodes"]:
            if node["id"] == failed_node_id:
                failed_node = node
                break
        if not failed_node:
            logger.warning(f"Failed node {failed_node_id} not found in graph")
            return graph

        # 3. Find predecessor Coder node by walking edges backwards
        coder_node_id = None
        queue = [failed_node_id]
        visited = set()
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            for edge in new_graph["edges"]:
                if edge["target"] == curr:
                    src = edge["source"]
                    src_node = None
                    for n in new_graph["nodes"]:
                        if n["id"] == src:
                            src_node = n
                            break
                    if src_node:
                        agent_type = src_node.get("data", {}).get("agentType") or src_node.get("type")
                        if agent_type in ["coder", "CoderAgent"]:
                            coder_node_id = src
                            break
                        queue.append(src)
            if coder_node_id:
                break

        if not coder_node_id:
            logger.warning(f"Predecessor CoderAgent node not found for failed node {failed_node_id}")
            return graph

        # 4. Create new debugger node
        failed_pos = failed_node.get("position", {"x": 0, "y": 0})
        debugger_node = {
            "id": f"healer_debug_{uuid.uuid4().hex[:8]}",
            "type": "agentNode",
            "data": {
                "label": "Auto-Healer: DebuggerAgent",
                "agentType": "debugger",
                "spawned_by_healing": True,
                "cycle": cycle_number,
                "error_context": error_context,
                "color": "#f59e0b",
                "icon": "🔧"
            },
            "position": {
                "x": failed_pos.get("x", 0) + 100,
                "y": failed_pos.get("y", 0) + 150
            }
        }

        # 5. Rewire edges
        failed_to_debugger_edge = {
            "id": f"heal_edge_{uuid.uuid4().hex[:8]}",
            "source": failed_node_id,
            "target": debugger_node["id"],
            "data": { "healing": True }
        }

        retry_edge_to_coder = {
            "id": f"heal_edge_{uuid.uuid4().hex[:8]}",
            "source": debugger_node["id"],
            "target": coder_node_id,
            "data": { "healing": True }
        }

        new_graph["nodes"].append(debugger_node)
        new_graph["edges"].append(failed_to_debugger_edge)
        new_graph["edges"].append(retry_edge_to_coder)

        return new_graph

graph_executor = GraphExecutor()
