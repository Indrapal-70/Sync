import { create } from 'zustand'
import { workflowService } from '../services/workflowService.js'

const useWorkflowStore = create((set, get) => ({
  workflows: [],
  selectedWorkflow: null,
  isLoading: false,
  error: null,
  fetchWorkflows: async () => {
    set({ isLoading: true, error: null })
    try {
      const workflows = await workflowService.getAll()
      set({ workflows, isLoading: false })
    } catch (error) {
      set({ error: error?.message || 'Failed to load workflows', isLoading: false })
    }
  },
  fetchWorkflow: async (id) => {
    set({ isLoading: true, error: null })
    try {
      const workflow = await workflowService.getById(id)
      const workflows = get().workflows
      const existing = workflows.find((item) => item.id === workflow.id)
      set({
        selectedWorkflow: workflow,
        workflows: existing
          ? workflows.map((item) => (item.id === workflow.id ? workflow : item))
          : [workflow, ...workflows],
        isLoading: false,
      })
    } catch (error) {
      set({ error: error?.message || 'Failed to load workflow', isLoading: false })
    }
  },
  createWorkflow: async (data) => {
    set({ isLoading: true, error: null })
    try {
      const created = await workflowService.create(data)
      set({
        workflows: [created, ...get().workflows],
        selectedWorkflow: created,
        isLoading: false,
      })
      return created
    } catch (error) {
      set({ error: error?.message || 'Failed to create workflow', isLoading: false })
      throw error
    }
  },
  updateWorkflow: async (id, data) => {
    set({ isLoading: true, error: null })
    try {
      const updated = await workflowService.update(id, data)
      set({
        workflows: get().workflows.map((item) => (item.id === id ? updated : item)),
        selectedWorkflow: get().selectedWorkflow?.id === id ? updated : get().selectedWorkflow,
        isLoading: false,
      })
    } catch (error) {
      set({ error: error?.message || 'Failed to update workflow', isLoading: false })
    }
  },
  deleteWorkflow: async (id) => {
    set({ isLoading: true, error: null })
    try {
      await workflowService.delete(id)
      set({
        workflows: get().workflows.filter((item) => item.id !== id),
        selectedWorkflow: get().selectedWorkflow?.id === id ? null : get().selectedWorkflow,
        isLoading: false,
      })
    } catch (error) {
      set({ error: error?.message || 'Failed to delete workflow', isLoading: false })
    }
  },
  executeWorkflow: async (id) => {
    set({ isLoading: true, error: null })
    try {
      await workflowService.execute(id)
      set({ isLoading: false })
    } catch (error) {
      set({ error: error?.message || 'Failed to execute workflow', isLoading: false })
    }
  },
  fetchTimeline: async (id) => {
    try {
      const data = await workflowService.getTimeline(id)
      return data.timeline || []
    } catch (error) {
      console.error('Failed to fetch timeline', error)
      return []
    }
  },
  fetchSummary: async (id) => {
    try {
      return await workflowService.getSummary(id)
    } catch (error) {
      console.error('Failed to fetch summary', error)
      return null
    }
  },
  saveAsTemplate: async (id) => {
    try {
      return await workflowService.saveAsTemplate(id)
    } catch (error) {
      console.error('Failed to save as template', error)
      throw error
    }
  },
  handleWebSocketEvent: (message) => {
    if (!message?.event) return
    const { event, payload } = message
    if (event === 'workflow_created') {
      const existing = get().workflows.find((item) => item.id === payload.id)
      if (!existing) {
        set({ workflows: [payload, ...get().workflows] })
      }
    }
    if (event === 'workflow_updated') {
      set({
        workflows: get().workflows.map((item) =>
          item.id === payload.id ? { ...item, ...payload } : item,
        ),
        selectedWorkflow:
          get().selectedWorkflow?.id === payload.id
            ? { ...get().selectedWorkflow, ...payload }
            : get().selectedWorkflow,
      })
    }
    if (event === 'workflow_deleted') {
      set({
        workflows: get().workflows.filter((item) => item.id !== payload.id),
        selectedWorkflow: get().selectedWorkflow?.id === payload.id ? null : get().selectedWorkflow,
      })
    }
  },
}))

export default useWorkflowStore
