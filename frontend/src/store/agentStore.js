import { create } from 'zustand'

const useAgentStore = create((set, get) => ({
  agents: [],
  selectedAgent: null,
  activeCount: 0,
  totalDeployed: 0,
  setAgents: (agents) => {
    const active = agents.filter((agent) => agent.status !== 'idle').length
    set({ agents, activeCount: active, totalDeployed: agents.length })
  },
  fetchAgents: async () => {
    set({ agents: [], activeCount: 0, totalDeployed: 0 })
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
