import { create } from 'zustand'

const mockWorkflows = []

const useWorkflowStore = create(() => ({
  workflows: mockWorkflows,
  tasks: mockWorkflows.flatMap((workflow) => workflow.tasks),
}))

export default useWorkflowStore
