import { create } from 'zustand'

const mockAlerts = [
  {
    id: 'alert-1',
    type: 'memory',
    level: 'error',
    title: 'Memory Leak Detected',
    description: 'Node SYN-CORE-03 exceeding memory threshold (92%).',
    timeAgo: '2 mins ago',
  },
  {
    id: 'alert-2',
    type: 'warning',
    level: 'warning',
    title: 'API Rate Limit Nearing',
    description: 'External service GitHub API at 85% capacity for this hour.',
    timeAgo: '15 mins ago',
  },
  {
    id: 'alert-3',
    type: 'success',
    level: 'info',
    title: 'Agent Deployed Successfully',
    description: 'SYN-QA-04 initialized and assigned to Workflow Beta.',
    timeAgo: '1 hour ago',
  },
]

const mockLogs = [
  {
    id: 'log-1',
    agentId: 'SYN-CORE-01',
    nodeId: 'processor-1',
    time: '10:42:01',
    level: 'INFO',
    message: 'Initializing environment sequence...',
  },
  {
    id: 'log-2',
    agentId: 'SYN-CORE-01',
    nodeId: 'processor-1',
    time: '10:42:02',
    level: 'SUCCESS',
    message: 'Dependencies loaded (142ms)',
  },
  {
    id: 'log-3',
    agentId: 'SYN-CORE-01',
    nodeId: 'processor-1',
    time: '10:42:05',
    level: 'INFO',
    message: 'Beginning routine tasks mapping.',
  },
  {
    id: 'log-4',
    agentId: 'SYN-CORE-01',
    nodeId: 'processor-1',
    time: '10:42:15',
    level: 'WARN',
    message: 'Memory threshold approaching warning level (78%).',
  },
  {
    id: 'log-5',
    agentId: 'SYN-CORE-01',
    nodeId: 'processor-1',
    time: '10:42:18',
    level: 'INFO',
    message: 'Compiling routine sub-module alpha...',
  },
  {
    id: 'log-6',
    agentId: 'SYN-CORE-01',
    nodeId: 'processor-1',
    time: '10:42:21',
    level: 'EXEC',
    message: 'function parseDataStream(input_buffer) {',
  },
]

const useLogStore = create((set) => ({
  alerts: mockAlerts,
  logs: mockLogs,
  clearAlerts: () => set({ alerts: [] }),
}))

export default useLogStore
