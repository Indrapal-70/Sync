import { create } from 'zustand'

const mockAgents = [
  {
    id: 'SYN-CORE-01',
    name: 'Programmer Agent_v2.4',
    type: 'programmer',
    status: 'running',
    currentTask: 'Refactoring authentication middleware modules in main API repository.',
    cpu: 42,
    ram: '1.2GB',
    nodeId: 'us-east-1a',
    resources: {
      cpu: 42,
      ramPercent: 78,
      networkMBs: 12,
    },
  },
  {
    id: 'SYN-QA-04',
    name: 'Tester Agent',
    type: 'tester',
    status: 'analyzing',
    currentTask: 'Executing integration test suite against newly committed auth endpoints.',
    cpu: 78,
    ram: '2.4GB',
    nodeId: 'us-east-1b',
    resources: {
      cpu: 78,
      ramPercent: 64,
      networkMBs: 8,
    },
  },
  {
    id: 'SYN-DBG-02',
    name: 'Debugger Agent',
    type: 'debugger',
    status: 'idle',
    currentTask: 'Awaiting anomalous stack trace input from Orchestrator queue.',
    cpu: 2,
    ram: '512MB',
    nodeId: 'us-east-1c',
    resources: {
      cpu: 2,
      ramPercent: 18,
      networkMBs: 1,
    },
  },
]

const useAgentStore = create((set, get) => ({
  agents: mockAgents,
  selectedAgent: mockAgents[0],
  activeCount: mockAgents.filter((agent) => agent.status !== 'idle').length,
  totalDeployed: mockAgents.length,
  fetchAgents: async () => {
    set({
      agents: mockAgents,
      activeCount: mockAgents.filter((agent) => agent.status !== 'idle').length,
      totalDeployed: mockAgents.length,
    })
  },
  selectAgent: (id) => {
    const next = get().agents.find((agent) => agent.id === id) || null
    set({ selectedAgent: next })
  },
  handleWebSocketEvent: (msg) => {
    if (!msg) return
  },
}))

export default useAgentStore
