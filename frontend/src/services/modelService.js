import api from './api'

export const modelService = {
  getHealth: () =>
    api.get('/api/models/health').then(r => r.data),

  getSkills: () =>
    api.get('/api/models/skills').then(r => r.data),

  getStats: () =>
    api.get('/api/models/stats').then(r => r.data),
}
