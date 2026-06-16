# backend/app/services/context_buffer.py

import asyncio
import time
from dataclasses import dataclass
from typing import List, Dict, Optional
from app.services.redis_client import publish_event

@dataclass
class ContextEntry:
    agent_name: str
    step: int                    # execution step number (0-indexed)
    input_summary: str           # brief summary of what this agent received
    output_summary: str          # brief summary of what this agent produced
    status: str                  # "passed" | "failed" | "skipped"
    error_details: Optional[str] = None    # full sandbox stderr if failed, else None
    suggested_fix: Optional[str] = None    # DebuggerAgent's fix suggestion, if any
    timestamp: float = 0.0       # time.time()
    healing_cycle: int = 0       # which healing cycle this belongs to

class AgentContextBuffer:
    def __init__(self, max_entries_per_task: int = 20):
        self._store: Dict[str, List[ContextEntry]] = {}
        self._lock = asyncio.Lock()
        self._max_entries = max_entries_per_task

    async def add_entry(self, task_id: str, entry: ContextEntry) -> None:
        """Thread-safe append. Trims to max_entries_per_task (oldest removed first)."""
        async with self._lock:
            tid_str = str(task_id)
            if entry.timestamp == 0.0:
                entry.timestamp = time.time()
            
            entries = self._store.setdefault(tid_str, [])
            entries.append(entry)
            
            # Trim buffer
            if len(entries) > self._max_entries:
                self._store[tid_str] = entries[-self._max_entries:]

        # Broadcast context_updated WebSocket event
        publish_event("context_updated", {
            "task_id": tid_str,
            "agent": entry.agent_name,
            "step": entry.step
        })

    async def get_context_for_agent(
        self,
        task_id: str,
        requesting_agent: str,
        last_n: int = 5,
    ) -> List[ContextEntry]:
        """
        Return the last N entries for this task that are RELEVANT to the
        requesting agent. Relevance rules:
        - CoderAgent: returns all previous TesterAgent failures and DebuggerAgent suggestions.
        - DebuggerAgent: returns the most recent TesterAgent failure entry.
        - All others: return last N entries regardless of agent.
        """
        async with self._lock:
            tid_str = str(task_id)
            entries = self._store.get(tid_str, [])
            if not entries:
                return []

            req_upper = requesting_agent.upper()
            if "CODER" in req_upper:
                # Coder needs all previous Tester failures and Debugger suggestions
                filtered = [
                    e for e in entries 
                    if (e.agent_name.lower() in ["tester", "testeragent"] and e.status == "failed")
                    or (e.agent_name.lower() in ["debugger", "debuggeragent"])
                ]
                return filtered[-last_n:]
            
            elif "DEBUGGER" in req_upper:
                # Debugger needs the most recent Tester failure entry
                filtered = [
                    e for e in entries
                    if e.agent_name.lower() in ["tester", "testeragent"] and e.status == "failed"
                ]
                return filtered[-1:] if filtered else []
            
            else:
                # Default behavior
                return entries[-last_n:]

    async def build_context_prompt(
        self,
        task_id: str,
        requesting_agent: str,
    ) -> str:
        """
        Formats the relevant context entries into a human-readable string
        suitable for injection into an LLM prompt.
        """
        relevant = await self.get_context_for_agent(task_id, requesting_agent)
        if not relevant:
            return ""

        prompt_parts = ["## Previous Execution Context\n"]
        for entry in relevant:
            cycle_str = f"Cycle {entry.healing_cycle}"
            prompt_parts.append(f"### {cycle_str} \u2014 {entry.agent_name} [{entry.status.upper()}]")
            
            if entry.error_details:
                prompt_parts.append(f"**What went wrong**:\n{entry.error_details}\n")
            if entry.suggested_fix:
                prompt_parts.append(f"**Suggested fix**:\n{entry.suggested_fix}\n")
                
            if not entry.error_details and not entry.suggested_fix:
                prompt_parts.append(f"Output: {entry.output_summary}\n")

        return "\n".join(prompt_parts)

    async def clear(self, task_id: str) -> None:
        """Remove all entries for a task. Call when task completes or is cancelled."""
        async with self._lock:
            self._store.pop(str(task_id), None)

agent_context_buffer = AgentContextBuffer()
