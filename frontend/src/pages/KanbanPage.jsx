import { motion } from 'framer-motion'
import { MoreHorizontal, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import useTaskStore from '../store/taskStore.js'
import TaskKanbanCard from '../components/TaskKanbanCard.jsx'

const columns = [
  { key: 'pending', title: 'Backlog' },
  { key: 'running', title: 'In Progress' },
  { key: 'testing', title: 'Testing' },
  { key: 'completed', title: 'Done' },
]

function KanbanPage() {
  const { tasks } = useTaskStore()
  const [selectedAgents, setSelectedAgents] = useState([])
  const [search, setSearch] = useState('')

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      const matchesAgent =
        selectedAgents.length === 0 || selectedAgents.includes(task.agentType)
      const query = search.trim().toLowerCase()
      const matchesSearch =
        query.length === 0 ||
        task.title.toLowerCase().includes(query) ||
        task.description.toLowerCase().includes(query)
      return matchesAgent && matchesSearch
    })
  }, [tasks, selectedAgents, search])

  const grouped = useMemo(() => {
    return columns.reduce((acc, col) => {
      acc[col.key] = filteredTasks.filter((task) => task.status === col.key)
      return acc
    }, {})
  }, [filteredTasks])

  const toggleAgent = (agentType) => {
    setSelectedAgents((prev) =>
      prev.includes(agentType)
        ? prev.filter((item) => item !== agentType)
        : [...prev, agentType],
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="h-[calc(100vh-64px)] flex flex-col"
    >
      <div className="px-6 py-4 border-b border-[#2a2a2a] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-[#0f0f0f]">
        <div>
          <h2 className="text-[28px] font-semibold text-[#f0f0f0]">Active Workflows</h2>
          <p className="text-[14px] text-[#888888]">Kanban board view for agent tasks.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-2 py-1.5">
            <span className="text-[10px] uppercase tracking-widest text-[#888888] mr-2">
              Agents:
            </span>
            {['programmer', 'tester', 'debugger'].map((agent) => (
              <button
                key={agent}
                type="button"
                onClick={() => toggleAgent(agent)}
                className={`text-[10px] uppercase tracking-widest px-2 py-1 rounded border transition-colors ${
                  selectedAgents.includes(agent)
                    ? 'bg-[#4f6ef7] text-[#0a0a0a] border-[#4f6ef7]'
                    : 'bg-[#2a2a2a] text-[#f0f0f0] border-transparent hover:border-[#2a2a2a]'
                }`}
              >
                {agent}
              </button>
            ))}
          </div>
          <div className="relative">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#555555]"
            />
            <input
              className="bg-[#1a1a1a] border border-[#2a2a2a] focus:border-[#f0f0f0] focus:ring-1 focus:ring-[#f0f0f0] rounded-lg pl-9 pr-4 py-2 text-[12px] text-[#f0f0f0] w-full sm:w-64 transition-all"
              placeholder="Search tasks..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-x-auto overflow-y-hidden p-6 bg-[#0a0a0a]">
        <div className="flex gap-6 h-full min-w-max pb-4">
          {columns.map((column) => (
            <div key={column.key} className="w-80 flex flex-col shrink-0">
              <div className="flex items-center justify-between mb-4 px-1">
                <h3 className="text-[18px] font-semibold text-[#f0f0f0] flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full border border-[#2a2a2a]" />
                  {column.title}
                  <span className="bg-[#1a1a1a] px-2 py-0.5 rounded text-[10px] uppercase tracking-widest text-[#888888]">
                    {grouped[column.key].length}
                  </span>
                </h3>
                <button className="text-[#888888] hover:text-[#f0f0f0]" type="button">
                  <MoreHorizontal size={20} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto flex flex-col gap-4 pr-2 pb-10">
                {grouped[column.key].map((task) => (
                  <TaskKanbanCard key={task.id} task={task} />
                ))}
                {grouped[column.key].length === 0 && (
                  <div className="text-[12px] text-[#555555]">No tasks.</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

export default KanbanPage
