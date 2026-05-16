import { create } from 'zustand'

const mockAlerts = []

const mockLogs = []

const useLogStore = create((set) => ({
  alerts: mockAlerts,
  logs: mockLogs,
  clearAlerts: () => set({ alerts: [] }),
}))

export default useLogStore
