import api from './api'

export const taskService = {
  getAll: (workflowId) =>
    api
      .get('/api/tasks', {
        params: workflowId ? { workflow_id: workflowId } : {},
      })
      .then((r) => r.data),

  create: (data) => api.post('/api/tasks', data).then((r) => r.data),

  update: (id, data) => api.patch(`/api/tasks/${id}`, data).then((r) => r.data),

  delete: (id) => api.delete(`/api/tasks/${id}`).then((r) => r.data),

  getAgentOutput: (id) => api.get(`/api/tasks/${id}/agent-output`).then((r) => r.data),
}
