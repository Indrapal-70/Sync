from pydantic import BaseModel
from typing import List, Optional

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

class GraphExecuteResponse(BaseModel):
    workflow_id:  str
    task_count:   int
    exec_order:   List[str]  # node names in topological execution order
    message:      str
