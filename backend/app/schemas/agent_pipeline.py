from typing import Optional

from pydantic import BaseModel


class AgentOutput(BaseModel):
    agent_name: str
    stage: str
    content: str
    success: bool
    errors: list[str] = []
    suggestions: list[str] = []
    execution_time_ms: int


class TestResult(BaseModel):
    test_name: str
    passed: bool
    error_message: Optional[str] = None
    severity: str = "info"


class PipelineStatus(BaseModel):
    task_id: str
    workflow_id: str
    current_agent: str
    pipeline_stage: str
    retry_count: int
    test_results: list[TestResult]
    agent_outputs: dict[str, AgentOutput]
