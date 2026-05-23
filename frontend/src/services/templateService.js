import api from './api'

export const templateService = {
  getAll: () => api.get('/api/templates').then((r) => r.data),
  getById: (id) => api.get(`/api/templates/${id}`).then((r) => r.data),
  create: (data) => api.post('/api/templates', data).then((r) => r.data),
  delete: (id) => api.delete(`/api/templates/${id}`).then((r) => r.data),
  instantiate: (id) => api.post(`/api/templates/${id}/instantiate`).then((r) => r.data),
}
