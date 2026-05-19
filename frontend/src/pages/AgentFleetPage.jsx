import { motion } from 'framer-motion'
import { useEffect, useMemo } from 'react'
import { CheckCircle2, Clock, Loader2, Pause, RefreshCcw, Settings2, Cpu, Code2 } from 'lucide-react'
import { useParams } from 'react-router-dom'
import useAgentStore from '../store/agentStore.js'
import useTaskStore from '../store/taskStore.js'
import useModelStore from '../store/modelStore.js'
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
  const { modelHealth, skillStats, skills, fetchModelHealth } = useModelStore()

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const getAgentModel = (agentType) => {
    const builderAgents = ['coder', 'tester']
    return builderAgents.includes(agentType)
      ? 'deepseek-coder:6.7b'
      : 'mistral:latest'
  }

  const agentCards = useMemo(() => {
    const base = [
      { name: 'coder', label: 'Coder Agent', model: getAgentModel('coder') },
      { name: 'tester', label: 'Tester Agent', model: getAgentModel('tester') },
      { name: 'debugger', label: 'Debugger Agent', model: getAgentModel('debugger') },
      { name: 'reviewer', label: 'Reviewer Agent', model: getAgentModel('reviewer') },
      { name: 'planner', label: 'Planner Agent', model: getAgentModel('planner') },
    ]

    return base.map((agent) => {
      const activeTasks = tasks.filter(
        (t) => t.current_agent === agent.name && t.status === 'running',
      )
      const completedCount = tasks.filter(
        (t) => t.agent_output?.[agent.name] && t.status === 'completed',
      ).length
      const activeTask = activeTasks[0]

      return {
        id: agent.name,
        name: agent.name,
        label: agent.label,
        model: agent.model,
        status: activeTasks.length ? 'running' : 'idle',
        currentTask: activeTask?.name,
        nodeId: activeTask?.workflow_id || 'n/a',
        resources: { cpu: 42, ramPercent: 68, networkMBs: 12 },
        activeTasks,
        completedCount,
        currentStage: activeTask?.pipeline_stage,
      }
    })
  }, [tasks])

  useEffect(() => {
    if (agentCards.length) {
      setAgents(agentCards)
    }
  }, [agentCards, setAgents])

  useEffect(() => {
    if (id) {
      selectAgent(id)
    }
  }, [id, selectAgent])

  const activeAgent = selectedAgent || agentCards[0]
  const agentSubtasks = useMemo(() => {
    if (!activeAgent) return []
    return tasks.filter(
      (task) => task.current_agent === activeAgent.name || task.agent_name === activeAgent.name,
    )
  }, [tasks, activeAgent])

  if (!activeAgent) {
    return (
      <div className="p-6 text-[#888888]">No agent selected.</div>
    )
  }

  const thinkerStatus = modelHealth['mistral:latest']
  const builderStatus = modelHealth['deepseek-coder:6.7b']
  const planStats = skillStats['plan'] || {}
  const builderStats = skillStats['code'] || {} // Just as an example or fallback if needed

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="p-4 md:p-8 flex flex-col gap-6"
    >
      {/* Model Status Section */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[18px] text-[#f0f0f0] font-semibold">Model Status</h2>
          <button 
            onClick={fetchModelHealth}
            className="text-[12px] text-[#888888] hover:text-[#f0f0f0] flex items-center gap-1 uppercase tracking-widest border border-[#2a2a2a] px-3 py-1 rounded bg-[#1a1a1a]"
          >
            <RefreshCcw size={12} /> Refresh
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Card 1 — The Thinker */}
          <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-5 flex flex-col">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[#2a2a2a] rounded-lg">
                  <Cpu size={20} className="text-[#8b5cf6]" />
                </div>
                <div>
                  <h3 className="text-[14px] font-semibold text-[#f0f0f0]">mistral:latest</h3>
                  <p className="text-[11px] text-[#888888]">The Thinker</p>
                </div>
              </div>
              <div className="flex items-center gap-2 bg-[#2a2a2a]/50 px-2 py-1 rounded border border-[#2a2a2a]">
                <span className={`w-2 h-2 rounded-full ${thinkerStatus?.available ? 'bg-[#22c55e] animate-pulse' : 'bg-[#ef4444]'}`} />
                <span className="text-[10px] uppercase tracking-widest text-[#f0f0f0]">
                  {thinkerStatus?.available ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 mb-4 flex-wrap">
              {['plan', 'debug', 'review'].map(s => (
                <span key={s} className="px-2 py-0.5 bg-[#8b5cf6]/10 border border-[#8b5cf6]/20 text-[#8b5cf6] text-[10px] rounded">
                  {s}
                </span>
              ))}
            </div>
            <div className="mt-auto pt-4 border-t border-[#2a2a2a] flex justify-between items-center text-[12px]">
              <span className="text-[#888888]">Handles reasoning, planning and review</span>
              <span className="text-[#f0f0f0] font-mono">
                {planStats.avg_ms ? `Avg ${(planStats.avg_ms / 1000).toFixed(1)}s` : '--'}
              </span>
            </div>
          </div>

          {/* Card 2 — The Builder */}
          <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-5 flex flex-col">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[#2a2a2a] rounded-lg">
                  <Code2 size={20} className="text-[#4f6ef7]" />
                </div>
                <div>
                  <h3 className="text-[14px] font-semibold text-[#f0f0f0]">deepseek-coder:6.7b</h3>
                  <p className="text-[11px] text-[#888888]">The Builder</p>
                </div>
              </div>
              <div className="flex items-center gap-2 bg-[#2a2a2a]/50 px-2 py-1 rounded border border-[#2a2a2a]">
                <span className={`w-2 h-2 rounded-full ${builderStatus?.available ? 'bg-[#22c55e] animate-pulse' : 'bg-[#ef4444]'}`} />
                <span className="text-[10px] uppercase tracking-widest text-[#f0f0f0]">
                  {builderStatus?.available ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 mb-4 flex-wrap">
              {['code', 'test'].map(s => (
                <span key={s} className="px-2 py-0.5 bg-[#4f6ef7]/10 border border-[#4f6ef7]/20 text-[#4f6ef7] text-[10px] rounded">
                  {s}
                </span>
              ))}
            </div>
            <div className="mt-auto pt-4 border-t border-[#2a2a2a] flex justify-between items-center text-[12px]">
              <span className="text-[#888888]">Handles code generation and testing</span>
              <span className="text-[#f0f0f0] font-mono">
                {builderStats.avg_ms ? `Avg ${(builderStats.avg_ms / 1000).toFixed(1)}s` : '--'}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Skill Performance Section */}
      <section>
        <h2 className="text-[18px] text-[#f0f0f0] font-semibold mb-4">Skill Performance</h2>
        <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#111111] border-b border-[#2a2a2a]">
                <th className="py-3 px-4 text-[#888888] text-xs uppercase tracking-widest font-medium">Skill</th>
                <th className="py-3 px-4 text-[#888888] text-xs uppercase tracking-widest font-medium">Model</th>
                <th className="py-3 px-4 text-[#888888] text-xs uppercase tracking-widest font-medium text-right">Total Calls</th>
                <th className="py-3 px-4 text-[#888888] text-xs uppercase tracking-widest font-medium text-right">Avg Response</th>
                <th className="py-3 px-4 text-[#888888] text-xs uppercase tracking-widest font-medium text-right">Error Rate</th>
              </tr>
            </thead>
            <tbody>
              {['plan', 'code', 'test', 'debug', 'review'].map((skillName) => {
                const sData = skillStats[skillName] || { total_calls: 0, avg_ms: 0, error_rate: 0 }
                const skillDef = skills?.find(s => s.name === skillName)
                const modelName = skillDef ? skillDef.model : '--'
                return (
                  <tr key={skillName} className="border-b border-[#2a2a2a] hover:bg-[#1a1a1a]/50 transition-colors">
                    <td className="py-3 px-4 text-[13px] text-[#f0f0f0] font-medium">{skillName}</td>
                    <td className="py-3 px-4 text-[13px] text-[#888888] font-mono">{modelName}</td>
                    <td className="py-3 px-4 text-[13px] text-[#f0f0f0] text-right font-mono">
                      {sData.total_calls}
                    </td>
                    <td className="py-3 px-4 text-[13px] text-[#888888] text-right font-mono">
                      {sData.total_calls > 0 ? `${(sData.avg_ms / 1000).toFixed(1)}s` : '--'}
                    </td>
                    <td className="py-3 px-4 text-[13px] text-[#888888] text-right font-mono">
                      {sData.total_calls > 0 ? `${(sData.error_rate * 100).toFixed(1)}%` : '--'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Active Agent Section */}
      <h2 className="text-[18px] text-[#f0f0f0] font-semibold mt-4">Active Agent Status</h2>
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
            <p className="text-[11px] text-[#555555] font-mono mt-1">
              Model: {activeAgent.model} | Stage: {activeAgent.currentStage || 'idle'}
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
                    {task.pipeline_stage && (
                      <p className="text-[10px] text-[#555555] mt-2 font-mono">
                        Stage: {task.pipeline_stage}
                      </p>
                    )}
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
