import { create } from 'zustand'

const useLogStore = create((set, get) => ({
  logs: [],
  maxLogs: 500,
  addLog: (log) => {
    const next = [log, ...get().logs]
    set({ logs: next.slice(0, get().maxLogs) })
  },
  clearLogs: () => set({ logs: [] }),
  getLogsByWorkflow: (workflowId) =>
    get().logs.filter((log) => log.workflow_id === workflowId),
  handleWebSocketEvent: (message) => {
    if (!message?.event) return
    if (message.event === 'log_created') {
      get().addLog(message.payload)
    }
  },
}))

export default useLogStore
