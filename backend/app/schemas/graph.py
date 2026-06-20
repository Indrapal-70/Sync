from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class FailurePolicy(str, Enum):
    HALT = "halt"           # existing behavior
    RETRY = "retry"         # simple retry same agent, up to N times
    HEAL = "heal"           # insert Debugger -> loop to Coder

class HealingConfig:
    max_healing_cycles: int = 3   # prevent infinite loops
    retry_limit: int = 2          # for RETRY policy


class NodeBlueprint(BaseModel):
    node_id:              str
    name:                 str
    description:          str
    agent_hint:           str              # "coder", "tester", etc.
    expected_output:      Optional[str]   = None
    max_retries_override: Optional[int]   = None
    dependencies:         List[str]       = []  # list of node_ids

class GraphExecuteRequest(BaseModel):
    workflow_name:   str
    workflow_desc:   Optional[str]   = ""
    nodes:           List[NodeBlueprint]
    source:          str            = "visual_editor"
    raw_graph:       Optional[dict] = None
    failure_policy:  Optional[FailurePolicy] = FailurePolicy.HALT

class GraphExecuteResponse(BaseModel):
    workflow_id:  str
    task_count:   int
    exec_order:   List[str]  # node names in topological execution order
    message:      str
    queue_position: Optional[int] = None
