import { create } from 'zustand'

const useSystemStore = create((set) => ({
  metrics: null,
  loading: false,
  error: null,

  fetchMetrics: async () => {
    set({ loading: true })
    try {
      const response = await fetch('http://localhost:8000/api/system/metrics')
      if (!response.ok) throw new Error('Failed to fetch metrics')
      const data = await response.json()
      set({ metrics: data, error: null })
    } catch (error) {
      console.error('Error fetching system metrics:', error)
      set({ error: error.message })
    } finally {
      set({ loading: false })
    }
  }
}))

export default useSystemStore
