import { Bot, Bug, Code2, FlaskConical } from 'lucide-react'
import StatusBadge from './StatusBadge.jsx'

const TYPE_CONFIG = {
  programmer: { label: 'PROGRAMMER', icon: Code2 },
  tester: { label: 'TESTER', icon: FlaskConical },
  debugger: { label: 'DEBUGGER', icon: Bug },
  planner: { label: 'PLANNER', icon: Bot },
}

function AgentCard({ agent }) {
  const config = TYPE_CONFIG[agent.type] || TYPE_CONFIG.programmer
  const Icon = config.icon
  const isRunning = agent.status === 'running'

  return (
    <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg p-5">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-[#2a2a2a] rounded-md">
            <Icon size={18} className="text-[#4f6ef7]" />
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-widest text-[#4f6ef7] bg-[#2a2a2a] px-2 py-0.5 rounded border border-[#2a2a2a] inline-block mb-1">
              {config.label}
            </div>
            <div className="font-mono text-[13px] text-[#f0f0f0]">{agent.id}</div>
          </div>
        </div>
        <StatusBadge status={agent.status} />
      </div>
      <div className="text-[14px] text-[#888888] mb-4 line-clamp-2">
        {agent.currentTask}
      </div>
      <div className="flex justify-between items-center pt-3 border-t border-[#2a2a2a]">
        <div className="text-[12px] text-[#888888]">
          CPU: {agent.cpu}% | RAM: {agent.ram}
        </div>
        <button className="text-[12px] text-[#4f6ef7] hover:text-[#f0f0f0] border-b border-transparent hover:border-[#4f6ef7] transition-colors">
          {isRunning ? 'View Logs' : 'Wake Agent'}
        </button>
      </div>
    </div>
  )
}

export default AgentCard
