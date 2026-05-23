import { create } from 'zustand'
import { taskService } from '../services/taskService.js'

const useTaskStore = create((set, get) => ({
  tasks: [],
  isLoading: false,
  fetchTasks: async (workflowId) => {
    set({ isLoading: true })
    try {
      const tasks = await taskService.getAll(workflowId)
      set({ tasks, isLoading: false })
    } catch (error) {
      set({ isLoading: false })
    }
  },
  createTask: async (data) => {
    set({ isLoading: true })
    try {
      const created = await taskService.create(data)
      set({ tasks: [...get().tasks, created], isLoading: false })
    } catch (error) {
      set({ isLoading: false })
    }
  },
  updateTask: async (id, data) => {
    set({ isLoading: true })
    try {
      const updated = await taskService.update(id, data)
      set({
        tasks: get().tasks.map((task) => (task.id === id ? updated : task)),
        isLoading: false,
      })
    } catch (error) {
      set({ isLoading: false })
    }
  },
  deleteTask: async (id) => {
    set({ isLoading: true })
    try {
      await taskService.delete(id)
      set({ tasks: get().tasks.filter((task) => task.id !== id), isLoading: false })
    } catch (error) {
      set({ isLoading: false })
    }
  },
  fetchAgentOutput: async (id) => {
    try {
      return await taskService.getAgentOutput(id)
    } catch (error) {
      console.error('Failed to fetch agent output', error)
      return null
    }
  },
  handleWebSocketEvent: (message) => {
    if (!message?.event) return
    const { event, payload } = message
    if (event === 'task_created') {
      const existing = get().tasks.find((task) => task.id === payload.id)
      if (!existing) {
        set({ tasks: [...get().tasks, payload] })
      }
    }
    if (event === 'task_updated') {
      set({
        tasks: get().tasks.map((task) => (task.id === payload.id ? { ...task, ...payload } : task)),
      })
    }
    if (event === 'task_deleted') {
      set({ tasks: get().tasks.filter((task) => task.id !== payload.id) })
    }
    if (event === 'agent_status_changed') {
      set({
        tasks: get().tasks.map((task) =>
          task.id === payload.task_id
            ? {
                ...task,
                current_agent: payload.agent_name,
                pipeline_stage: payload.pipeline_stage,
              }
            : task,
        ),
      })
    }
  },
  getTasksByWorkflow: (workflowId) =>
    get().tasks.filter((task) => task.workflow_id === workflowId),
}))

export default useTaskStore
