import { create } from 'zustand'

const mockWorkflows = [
  {
    id: 'workflow-1',
    name: 'Task Divider Bot',
    tasks: [
      { id: 'TSK-8892', status: 'completed' },
      { id: 'TSK-8893', status: 'completed' },
      { id: 'TSK-8894', status: 'completed' },
      { id: 'TSK-8895', status: 'completed' },
      { id: 'TSK-8896', status: 'completed' },
      { id: 'TSK-8897', status: 'completed' },
      { id: 'TSK-8898', status: 'completed' },
      { id: 'TSK-8899', status: 'completed' },
      { id: 'TSK-8900', status: 'completed' },
      { id: 'TSK-8901', status: 'completed' },
      { id: 'TSK-8902', status: 'completed' },
      { id: 'TSK-8903', status: 'completed' },
      { id: 'TSK-8904', status: 'completed' },
      { id: 'TSK-8905', status: 'completed' },
    ],
  },
]

const useWorkflowStore = create(() => ({
  workflows: mockWorkflows,
  tasks: mockWorkflows.flatMap((workflow) => workflow.tasks),
}))

export default useWorkflowStore
