import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, TrendingDown, TrendingUp } from 'lucide-react'
import useAgentStore from '../store/agentStore.js'
import useWorkflowStore from '../store/workflowStore.js'
import useTaskStore from '../store/taskStore.js'
import useLogStore from '../store/logStore.js'
import useModelStore from '../store/modelStore.js'
import AgentCard from '../components/AgentCard.jsx'
import { Cpu, Terminal, Send, HardDrive, Activity } from 'lucide-react'
import useSystemStore from '../store/systemStore.js'


const MODEL_CONFIG = {
  'mistral:latest': {},
  'deepseek-coder:6.7b': {}
}

function OrchestrationPage() {
  const { agents, activeCount, totalDeployed, setAgents } = useAgentStore()
  const { workflows, fetchWorkflows } = useWorkflowStore()
  const { modelHealth, allModelsOk, fallbackActive } = useModelStore()
  const { metrics, fetchMetrics } = useSystemStore()
  const { tasks: taskList, fetchTasks } = useTaskStore()
  const { logs } = useLogStore()
  const [command, setCommand] = useState('')
  const [isCommandRunning, setIsCommandRunning] = useState(false)

  useEffect(() => {
    fetchWorkflows()
    fetchTasks()
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 5000)
    return () => clearInterval(interval)
  }, [fetchWorkflows, fetchTasks, fetchMetrics])

  const handleRunCommand = async (e) => {
    e.preventDefault()
    if (!command.trim()) return
    setIsCommandRunning(true)
    try {
      const res = await fetch('http://localhost:8000/api/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Terminal Command', description: command })
      })
      if (!res.ok) throw new Error('Failed to create workflow')
      const data = await res.json()
      
      const execRes = await fetch(`http://localhost:8000/api/workflows/${data.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
      if (!execRes.ok) throw new Error('Failed to execute workflow')
      setCommand('')
      fetchWorkflows()
    } catch (err) {
      console.error(err)
    } finally {
      setIsCommandRunning(false)
    }
  }

  useEffect(() => {
    const runningTasks = taskList.filter((task) => task.status === 'running')
    const agentMap = new Map()
    runningTasks.forEach((task, index) => {
      const agentKey = task.current_agent || task.agent_name || `agent-${index}`
      if (!agentMap.has(agentKey)) {
        const inferredType = task.current_agent || task.agent_name || 'coder'
        agentMap.set(agentKey, {
          id: agentKey,
          name: agentKey || 'Unassigned',
          type: inferredType,
          status: 'running',
          currentTask: task.name,
          nodeId: task.workflow_id,
          cpu: 42,
          ram: '68%',
        })
      }
    })
    setAgents(Array.from(agentMap.values()))
  }, [taskList, setAgents])

  const totalWorkflows = workflows.length
  const completedWorkflows = workflows.filter((workflow) => workflow.status === 'completed').length
  const successRate = totalWorkflows
    ? Math.round((completedWorkflows / totalWorkflows) * 1000) / 10
    : 0
  const failedWorkflows = useMemo(
    () => workflows.filter((workflow) => workflow.status === 'failed').length,
    [workflows],
  )
  const filteredAlerts = useMemo(
    () => logs.filter((log) => ['warning', 'error'].includes(log.level)),
    [logs],
  )
  
  // Calculate system health
  const recentErrorLogs = logs.filter(
    log => log.level === 'error' && (Date.now() - new Date(log.created_at).getTime()) < 5 * 60 * 1000
  )
  
  const onlineModels = Object.values(modelHealth || {}).filter(m => m.available).length
  const totalModels = Object.keys(MODEL_CONFIG).length
  
  const isOptimal = allModelsOk && recentErrorLogs.length === 0
  const isError = !allModelsOk && onlineModels === 0
  const isDegraded = (onlineModels > 0 && onlineModels < totalModels) || fallbackActive

  const totalWorkflowsCount = workflows.length

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="p-4 md:p-8"
    >
      <div className="max-w-[1440px] mx-auto space-y-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-[28px] md:text-[32px] font-semibold text-[#f0f0f0]">
              Orchestration Overview
            </h1>
            <p className="text-[14px] text-[#888888] mt-2 max-w-2xl">
              Monitor active agent fleets, workflow execution health, and system-wide
              orchestration metrics in real-time.
            </p>
          </div>
          {isOptimal && (
            <div className="flex items-center gap-2 text-[#22c55e]">
              <CheckCircle2 size={16} />
              <span className="text-[10px] uppercase tracking-widest text-[#22c55e]">System Optimal</span>
            </div>
          )}
          {isError && (
            <div className="flex items-center gap-2 text-[#ef4444]">
              <Cpu size={16} />
              <span className="text-[10px] uppercase tracking-widest text-[#ef4444]">System Error</span>
            </div>
          )}
          {isDegraded && !isError && (
            <div className="flex items-center gap-2 text-[#f59e0b]">
              <Cpu size={16} />
              <span className="text-[10px] uppercase tracking-widest text-[#f59e0b]">Degraded</span>
            </div>
          )}
        </div>

        {/* Command Palette */}
        <div className="bg-[#111111] border border-[#2a2a2a] rounded-xl p-4 flex flex-col md:flex-row items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-[#4f6ef7]/10 flex items-center justify-center shrink-0">
            <Terminal size={18} className="text-[#4f6ef7]" />
          </div>
          <form onSubmit={handleRunCommand} className="flex-1 flex w-full">
            <input
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              placeholder="Enter a prompt to trigger a local agent workflow..."
              className="flex-1 bg-transparent border-none outline-none text-[#f0f0f0] text-[14px] placeholder:text-[#555]"
              disabled={isCommandRunning}
            />
            <button
              type="submit"
              disabled={isCommandRunning || !command.trim()}
              className="ml-4 px-4 py-2 bg-[#4f6ef7] hover:bg-[#3d5ae6] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg flex items-center gap-2 text-[12px] font-medium transition-colors"
            >
              {isCommandRunning ? 'Processing...' : 'Run'} <Send size={14} />
            </button>
          </form>
        </div>

        {/* System Metrics */}
        {metrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-4 flex items-center gap-4">
              <Activity size={24} className="text-[#888888]" />
              <div>
                <div className="text-[10px] uppercase tracking-widest text-[#888888]">CPU Usage</div>
                <div className="text-[18px] font-semibold text-[#f0f0f0]">{metrics.cpu?.percent.toFixed(1)}%</div>
              </div>
            </div>
            <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-4 flex items-center gap-4">
              <HardDrive size={24} className="text-[#888888]" />
              <div>
                <div className="text-[10px] uppercase tracking-widest text-[#888888]">RAM Usage</div>
                <div className="text-[18px] font-semibold text-[#f0f0f0]">{metrics.ram?.percent.toFixed(1)}% ({metrics.ram?.used_gb} / {metrics.ram?.total_gb} GB)</div>
              </div>
            </div>
            {metrics.gpu && (
              <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-4 flex items-center gap-4">
                <Cpu size={24} className="text-[#888888]" />
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-[#888888]">GPU ({metrics.gpu.name})</div>
                  <div className="text-[18px] font-semibold text-[#f0f0f0]">{metrics.gpu.percent.toFixed(1)}% Util</div>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] uppercase tracking-widest text-[#888888]">
                Total Workflows
              </span>
              <CheckCircle2 size={18} className="text-[#4f6ef7]" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-[32px] text-[#f0f0f0] font-semibold">{totalWorkflowsCount}</span>
              <span className="text-[10px] text-[#4f6ef7] flex items-center gap-1">
                <TrendingUp size={14} /> 12%
              </span>
            </div>
            <div className="mt-4 w-full bg-[#2a2a2a] h-1 rounded-full overflow-hidden">
              <div className="bg-[#4f6ef7] h-full w-3/4 rounded-full" />
            </div>
          </div>

          <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] uppercase tracking-widest text-[#888888]">
                Active Agents
              </span>
              <CheckCircle2 size={18} className="text-[#4f6ef7]" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-[32px] text-[#f0f0f0] font-semibold">{activeCount}</span>
              <span className="text-[12px] text-[#888888]">/ {totalDeployed} deployed</span>
            </div>
            <div className="mt-4 flex gap-1">
              {Array.from({ length: totalDeployed }).map((_, index) => (
                <div
                  key={index}
                  className={`h-1 flex-1 rounded-full ${
                    index < activeCount ? 'bg-[#4f6ef7]' : 'bg-[#2a2a2a]'
                  }`}
                />
              ))}
            </div>
          </div>

          <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] uppercase tracking-widest text-[#888888]">
                Success Rate
              </span>
              <CheckCircle2 size={18} className="text-[#4f6ef7]" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-[32px] text-[#f0f0f0] font-semibold">
                {successRate}%
              </span>
              <span className="text-[10px] text-[#4f6ef7] flex items-center gap-1">
                <TrendingDown size={14} /> 0.2%
              </span>
            </div>
            <div className="mt-4 w-full h-8 flex items-end gap-1">
              {Array.from({ length: 6 }).map((_, idx) => (
                <div
                  key={idx}
                  className="w-1/6 bg-[#2a2a2a] h-full rounded-t-sm"
                />
              ))}
            </div>
          </div>

          {/* Models Online Card */}
          <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] uppercase tracking-widest text-[#888888]">
                Models Online
              </span>
              <Cpu size={18} className={
                onlineModels === totalModels ? "text-[#22c55e]" : 
                onlineModels > 0 ? "text-[#f59e0b]" : "text-[#ef4444]"
              } />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-[32px] text-[#f0f0f0] font-semibold">
                {onlineModels} / {totalModels}
              </span>
              {fallbackActive && (
                <span className="text-[10px] text-[#f59e0b] ml-2 uppercase tracking-widest">
                  Fallback
                </span>
              )}
            </div>
            <div className="mt-4 flex gap-1">
              {Array.from({ length: totalModels }).map((_, index) => (
                <div
                  key={index}
                  className={`h-1 flex-1 rounded-full ${
                    index < onlineModels ? (onlineModels === totalModels ? 'bg-[#22c55e]' : 'bg-[#f59e0b]') : 'bg-[#2a2a2a]'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-[18px] text-[#f0f0f0] border-b border-[#2a2a2a] pb-2">
              Active Agent Fleet
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {agents.map((agent) => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl overflow-hidden flex flex-col h-full max-h-[400px]">
              <div className="p-4 border-b border-[#2a2a2a] flex justify-between items-center bg-[#111111]">
                <h3 className="text-[18px] text-[#f0f0f0]">Recent Alerts</h3>
                <span className="text-[10px] uppercase tracking-widest text-[#4f6ef7]">
                  Live Feed
                </span>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {filteredAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="p-3 bg-[#2a2a2a]/40 border border-[#2a2a2a] rounded-lg flex gap-3 items-start"
                  >
                    <div
                      className={`w-2 h-2 mt-2 rounded-full ${
                        alert.level === 'error'
                          ? 'bg-[#ef4444]'
                          : alert.level === 'warning'
                            ? 'bg-[#f59e0b]'
                            : 'bg-[#4f6ef7]'
                      }`}
                    />
                    <div>
                      <div className="text-[12px] font-semibold text-[#f0f0f0]">
                        {alert.level.toUpperCase()}
                      </div>
                      <div className="font-mono text-[12px] text-[#888888] mt-1">
                        {alert.message}
                      </div>
                      <div className="text-[10px] text-[#888888] mt-2">
                        {new Date(alert.created_at).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
                {filteredAlerts.length === 0 && (
                  <div className="text-[12px] text-[#555555] p-4">No alerts.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default OrchestrationPage
