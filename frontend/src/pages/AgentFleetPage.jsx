import { motion } from 'framer-motion'
import { useEffect, useMemo } from 'react'
import { CheckCircle2, Clock, Loader2, Pause, RefreshCcw, Settings2 } from 'lucide-react'
import { useParams } from 'react-router-dom'
import useAgentStore from '../store/agentStore.js'
import useTaskStore from '../store/taskStore.js'
import ExecutionLogPanel from '../components/ExecutionLogPanel.jsx'

function getBarColor(value) {
  if (value > 90) return 'bg-[#ef4444]'
  if (value > 70) return 'bg-[#f59e0b]'
  return 'bg-[#4f6ef7]'
}

function AgentFleetPage() {
  const { id } = useParams()
  const { selectedAgent, selectAgent, setAgents } = useAgentStore()
  const { tasks, fetchTasks } = useTaskStore()

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const runningTasks = useMemo(() => tasks.filter((task) => task.status === 'running'), [tasks])
  const agentMap = useMemo(() => {
    const map = new Map()
    runningTasks.forEach((task, index) => {
      const key = task.agent_name || `agent-${index}`
      if (!map.has(key)) {
        map.set(key, {
          id: key,
          name: task.agent_name || 'Unassigned',
          status: 'running',
          currentTask: task.name,
          nodeId: task.workflow_id,
          resources: { cpu: 42, ramPercent: 68, networkMBs: 12 },
        })
      }
    })
    return Array.from(map.values())
  }, [runningTasks])

  useEffect(() => {
    if (agentMap.length) {
      setAgents(agentMap)
    }
  }, [agentMap, setAgents])

  useEffect(() => {
    if (id) {
      selectAgent(id)
    }
  }, [id, selectAgent])

  const activeAgent = selectedAgent || agentMap[0]
  const agentSubtasks = useMemo(
    () => tasks.filter((task) => task.agent_name === activeAgent?.name),
    [tasks, activeAgent],
  )

  if (!activeAgent) {
    return (
      <div className="p-6 text-[#888888]">No agent selected.</div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="p-4 md:p-8 h-[calc(100vh-64px)] flex flex-col"
    >
      <div className="glass-panel bg-[#1a1a1a]/70 border border-[#2a2a2a] rounded-xl p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 border-t-4 border-t-[#4f6ef7]">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-[#2a2a2a] flex items-center justify-center border border-[#2a2a2a]">
            <span className="text-[#4f6ef7] font-semibold">{activeAgent.name[0]}</span>
          </div>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-[20px] font-semibold text-[#f0f0f0]">
                {activeAgent.name}
              </h2>
              <span className="px-2 py-1 rounded-full bg-[#0f1a3a] text-[#4f6ef7] border border-[#4f6ef7]/20 text-[10px] uppercase tracking-widest flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#22c55e] status-pulse" />
                Active
              </span>
            </div>
            <p className="text-[12px] text-[#888888] font-mono">
              ID: {activeAgent.id} | Node: {activeAgent.nodeId}
            </p>
          </div>
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <button className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded border border-[#2a2a2a] text-[#f0f0f0] hover:bg-[#1a1a1a] text-[12px] uppercase tracking-widest">
            <Pause size={16} /> Pause
          </button>
          <button className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded border border-[#2a2a2a] text-[#f0f0f0] hover:bg-[#1a1a1a] text-[12px] uppercase tracking-widest">
            <RefreshCcw size={16} /> Restart
          </button>
          <button className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded border border-[#4f6ef7] text-[#4f6ef7] hover:bg-[#0f1a3a] text-[12px] uppercase tracking-widest">
            <Settings2 size={16} /> Config
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 mt-6 min-h-0">
        <div className="lg:col-span-2 min-h-0">
          <ExecutionLogPanel agentId={activeAgent.nodeId} />
        </div>
        <div className="space-y-6 flex flex-col min-h-0">
          <div className="bg-[#1a1a1a]/70 border border-[#2a2a2a] rounded-xl p-4 flex-1">
            <h3 className="text-[12px] uppercase tracking-widest text-[#f0f0f0] mb-4">
              Resource Usage
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-[12px] mb-1 text-[#888888]">
                  <span>CPU Load</span>
                  <span className="text-[#f0f0f0]">{activeAgent.resources.cpu}%</span>
                </div>
                <div className="w-full bg-[#2a2a2a] rounded-full h-1.5">
                  <div
                    className={`${getBarColor(activeAgent.resources.cpu)} h-1.5 rounded-full`}
                    style={{ width: `${activeAgent.resources.cpu}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[12px] mb-1 text-[#888888]">
                  <span>Memory (RAM)</span>
                  <span className="text-[#f0f0f0]">{activeAgent.resources.ramPercent}%</span>
                </div>
                <div className="w-full bg-[#2a2a2a] rounded-full h-1.5">
                  <div
                    className={`${getBarColor(activeAgent.resources.ramPercent)} h-1.5 rounded-full`}
                    style={{ width: `${activeAgent.resources.ramPercent}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[12px] mb-1 text-[#888888]">
                  <span>Network I/O</span>
                  <span className="text-[#f0f0f0]">{activeAgent.resources.networkMBs}MB/s</span>
                </div>
                <div className="w-full bg-[#2a2a2a] rounded-full h-1.5">
                  <div
                    className="bg-[#888888] h-1.5 rounded-full"
                    style={{ width: '25%' }}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-[#1a1a1a]/70 border border-[#2a2a2a] rounded-xl p-4 flex-1 flex flex-col min-h-0">
            <h3 className="text-[12px] uppercase tracking-widest text-[#f0f0f0] mb-4">
              Current Sub-tasks
            </h3>
            <div className="space-y-3 overflow-y-auto flex-1">
              {agentSubtasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-start gap-3 p-3 rounded-lg bg-[#2a2a2a]/40 border border-[#2a2a2a]"
                >
                  {task.status === 'completed' && (
                    <CheckCircle2 size={18} className="text-[#22c55e]" />
                  )}
                  {task.status === 'running' && (
                    <Loader2 size={18} className="text-[#4f6ef7] animate-spin" />
                  )}
                  {task.status === 'pending' && (
                    <Clock size={18} className="text-[#888888]" />
                  )}
                  <div>
                    <p className="text-[12px] text-[#f0f0f0]">{task.name}</p>
                    <p className="text-[11px] text-[#888888] mt-1">{task.description}</p>
                  </div>
                </div>
              ))}
              {agentSubtasks.length === 0 && (
                <div className="text-[12px] text-[#555555]">No tasks assigned.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default AgentFleetPage
