import { create } from 'zustand'

const mockTasks = []

const mockSubtasks = []

const useTaskStore = create(() => ({
  tasks: mockTasks,
  subtasks: mockSubtasks,
}))

export default useTaskStore
