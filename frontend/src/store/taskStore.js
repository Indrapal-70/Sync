import { create } from 'zustand'

const mockTasks = [
  {
    id: 'TASK-842',
    title: 'Implement Auth Middleware',
    description:
      'Develop JWT-based authentication middleware for the primary API gateway to secure incoming orchestrator requests.',
    status: 'pending',
    agentId: 'SYN-CORE-01',
    agentType: 'programmer',
    workflowId: 'workflow-1',
  },
  {
    id: 'TASK-845',
    title: 'Load Testing Node Clusters',
    description: 'Simulate 10k concurrent agent connections to identify bottleneck in the websocket layer.',
    status: 'pending',
    agentId: 'SYN-QA-04',
    agentType: 'tester',
    workflowId: 'workflow-1',
  },
  {
    id: 'TASK-831',
    title: 'Optimize Vector Search',
    description:
      'Refactor the embeddings indexing process to reduce memory footprint during semantic search queries.',
    status: 'running',
    progress: 65,
    agentId: 'SYN-CORE-01',
    agentType: 'programmer',
    workflowId: 'workflow-1',
  },
  {
    id: 'ISSUE-112',
    title: 'Memory Leak in Node 4',
    description:
      'Investigate isolated memory spike in agent orchestration node 4 during concurrent workflow execution.',
    status: 'running',
    progress: 30,
    warning: true,
    agentId: 'SYN-DBG-02',
    agentType: 'debugger',
    workflowId: 'workflow-1',
  },
  {
    id: 'TASK-820',
    title: 'E2E Workflow Validation',
    description:
      'Run comprehensive E2E tests on the newly deployed multi-agent reasoning workflow.',
    status: 'testing',
    coverage: 92,
    agentId: 'SYN-QA-04',
    agentType: 'tester',
    workflowId: 'workflow-1',
  },
  {
    id: 'TASK-815',
    title: 'Update Dependencies',
    description: 'Bump core orchestration libraries to latest stable versions.',
    status: 'completed',
    agentId: 'SYN-CORE-01',
    agentType: 'programmer',
    workflowId: 'workflow-1',
  },
]

const mockSubtasks = [
  {
    id: 'sub-1',
    agentId: 'SYN-CORE-01',
    title: 'Parse raw JSON inputs',
    status: 'completed',
    detail: 'Completed in 45ms',
  },
  {
    id: 'sub-2',
    agentId: 'SYN-CORE-01',
    title: 'Compile AST for core module',
    status: 'running',
    detail: 'Running... (1.2s)',
  },
  {
    id: 'sub-3',
    agentId: 'SYN-CORE-01',
    title: 'Execute unit tests',
    status: 'queued',
    detail: 'Queued',
  },
]

const useTaskStore = create(() => ({
  tasks: mockTasks,
  subtasks: mockSubtasks,
}))

export default useTaskStore
