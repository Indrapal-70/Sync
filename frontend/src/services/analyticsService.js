import api from './api'

export const analyticsService = {
  getAgentPerformance: (days = 7) => api.get(`/api/analytics/agent-performance`, { params: { days } }).then((r) => r.data),
  getHealingSummary: (days = 7) => api.get(`/api/analytics/healing-summary`, { params: { days } }).then((r) => r.data),
  getTaskTimeline: (taskId) => api.get(`/api/analytics/task-timeline/${taskId}`).then((r) => r.data),
}
