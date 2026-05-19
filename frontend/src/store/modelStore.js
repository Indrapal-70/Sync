import { create } from 'zustand'
import { modelService } from '../services/modelService'

const useModelStore = create((set, get) => ({
  modelHealth: {},      // { "mistral:latest": {available, response_ms, error}, ... }
  skills: [],           // array of skill info objects
  skillStats: {},       // { "plan": {total_calls, avg_ms, error_rate}, ... }
  allModelsOk: false,
  isLoading: false,
  lastChecked: null,
  fallbackActive: false,
  activeSkills: new Set(),
  config: null,

  fetchModelHealth: async () => {
    try {
      const data = await modelService.getHealth()
      set({
        modelHealth: data.models || {},
        allModelsOk: data.all_models_ok || false,
        lastChecked: new Date().toISOString()
      })
    } catch (e) {
      console.error('[ModelStore] Health fetch failed:', e)
    }
  },

  fetchSkills: async () => {
    try {
      const data = await modelService.getSkills()
      set({ skills: Array.isArray(data) ? data : [] })
    } catch (e) {
      console.error('[ModelStore] Skills fetch failed:', e)
    }
  },

  fetchSkillStats: async () => {
    try {
      const data = await modelService.getStats()
      set({ skillStats: data || {} })
    } catch (e) {
      console.error('[ModelStore] Stats fetch failed:', e)
    }
  },

  fetchConfig: async () => {
    try {
      const data = await modelService.getConfig()
      set({ config: data })
    } catch (e) {
      console.error('[ModelStore] Config fetch failed:', e)
    }
  },

  fetchAll: async () => {
    set({ isLoading: true })
    await Promise.all([
      get().fetchModelHealth(),
      get().fetchSkills(),
      get().fetchSkillStats(),
      get().fetchConfig(),
    ])
    set({ isLoading: false })
  },

  handleWebSocketEvent: (message) => {
    const { event, payload } = message
    if (event === 'skill_reassigned') {
      set(state => ({
        skills: state.skills.map(s =>
          s.name === payload.skill_name
            ? { ...s, model: payload.new_model, model_key: payload.new_model_key }
            : s
        )
      }))
    }
    if (event === 'model_fallback_used') {
      set({ fallbackActive: true })
    }
    if (event === 'skill_called') {
      set(state => {
        const next = new Set(state.activeSkills)
        next.add(payload?.skill_name)
        return { activeSkills: next }
      })
    }
    if (event === 'skill_completed' || event === 'skill_failed') {
      set(state => {
        const next = new Set(state.activeSkills)
        next.delete(payload?.skill_name)
        return { activeSkills: next }
      })
      get().fetchSkillStats()
    }
  }
}))

export default useModelStore
