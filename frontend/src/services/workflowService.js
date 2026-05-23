import api from './api'

export const workflowService = {
  getAll: () => api.get('/api/workflows').then((r) => r.data),

  getById: (id) => api.get(`/api/workflows/${id}`).then((r) => r.data),

  create: (data) => api.post('/api/workflows', data).then((r) => r.data),

  update: (id, data) => api.patch(`/api/workflows/${id}`, data).then((r) => r.data),

  delete: (id) => api.delete(`/api/workflows/${id}`).then((r) => r.data),

  execute: (id) => api.post(`/api/workflows/${id}/execute`).then((r) => r.data),

  getTimeline: (id) => api.get(`/api/workflows/${id}/timeline`).then((r) => r.data),

  getSummary: (id) => api.get(`/api/workflows/${id}/summary`).then((r) => r.data),

  saveAsTemplate: (id) => api.post(`/api/workflows/${id}/save-as-template`).then((r) => r.data),
}
