import { create } from 'zustand'

const mockAgents = []

const useAgentStore = create((set, get) => ({
  agents: mockAgents,
  selectedAgent: null,
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
