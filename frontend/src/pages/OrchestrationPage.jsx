import { motion } from 'framer-motion'
import { CheckCircle2, TrendingDown, TrendingUp } from 'lucide-react'
import useAgentStore from '../store/agentStore.js'
import useWorkflowStore from '../store/workflowStore.js'
import useTaskStore from '../store/taskStore.js'
import useLogStore from '../store/logStore.js'
import AgentCard from '../components/AgentCard.jsx'

function OrchestrationPage() {
  const { agents, activeCount, totalDeployed } = useAgentStore()
  const { tasks } = useWorkflowStore()
  const { tasks: taskList } = useTaskStore()
  const { alerts, clearAlerts } = useLogStore()

  const completedTasks = taskList.filter((task) => task.status === 'completed').length
  const successRate = taskList.length
    ? Math.round((completedTasks / taskList.length) * 1000) / 10
    : 0
  const isHealthy = agents.every((agent) => agent.status !== 'error')

  const filteredAlerts = alerts.filter((alert) => ['warning', 'error'].includes(alert.level))

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
          {isHealthy && (
            <div className="flex items-center gap-2 text-[#22c55e]">
              <CheckCircle2 size={16} />
              <span className="text-[10px] uppercase tracking-widest">System Optimal</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] uppercase tracking-widest text-[#888888]">
                Total Tasks
              </span>
              <CheckCircle2 size={18} className="text-[#4f6ef7]" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-[32px] text-[#f0f0f0] font-semibold">{tasks.length}</span>
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
                <button
                  className="text-[10px] uppercase tracking-widest text-[#4f6ef7] hover:text-[#f0f0f0]"
                  type="button"
                  onClick={clearAlerts}
                >
                  Clear All
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {filteredAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="p-3 bg-[#2a2a2a]/40 border border-[#2a2a2a] rounded-lg flex gap-3 items-start"
                  >
                    <div
                      className={`w-2 h-2 mt-2 rounded-full ${
                        alert.type === 'memory'
                          ? 'bg-[#ef4444]'
                          : alert.type === 'warning'
                            ? 'bg-[#f59e0b]'
                            : 'bg-[#4f6ef7]'
                      }`}
                    />
                    <div>
                      <div className="text-[12px] font-semibold text-[#f0f0f0]">
                        {alert.title}
                      </div>
                      <div className="font-mono text-[12px] text-[#888888] mt-1">
                        {alert.description}
                      </div>
                      <div className="text-[10px] text-[#888888] mt-2">{alert.timeAgo}</div>
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
