import api from './api'

export const templateService = {
  getAll: () => api.get('/api/templates').then((r) => r.data),
  getById: (id) => api.get(`/api/templates/${id}`).then((r) => r.data),
  create: (data) => api.post('/api/templates', data).then((r) => r.data),
  delete: (id) => api.delete(`/api/templates/${id}`).then((r) => r.data),
  instantiate: (id) => api.post(`/api/templates/${id}/instantiate`).then((r) => r.data),
  getMarketplace: () => api.get('/api/templates/marketplace').then((r) => r.data),
  publish: (id, tags) => api.post(`/api/templates/${id}/publish`, { tags }).then((r) => r.data),
  fork: (id, data) => api.post(`/api/templates/${id}/fork`, data).then((r) => r.data),
  use: (id) => api.post(`/api/templates/${id}/use`).then((r) => r.data),
}

