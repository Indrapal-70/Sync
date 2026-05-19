import { Bot, Bug, Code2, FlaskConical } from 'lucide-react'
import StatusBadge from './StatusBadge.jsx'

const getAgentModel = (agentType) => {
  const builderAgents = ['coder', 'tester']
  return builderAgents.includes(agentType)
    ? 'deepseek-coder:6.7b'
    : 'mistral:latest'
}

const getModelDisplayName = (fullName) => {
  if (fullName.includes('deepseek')) return 'deepseek-coder'
  if (fullName.includes('mistral')) return 'mistral'
  return fullName.split(':')[0]
}

const TYPE_CONFIG = {
  coder: { label: 'CODER', icon: Code2 },
  tester: { label: 'TESTER', icon: FlaskConical },
  debugger: { label: 'DEBUGGER', icon: Bug },
  reviewer: { label: 'REVIEWER', icon: Code2 },
  planner: { label: 'PLANNER', icon: Bot },
}

function AgentCard({ agent }) {
  const config = TYPE_CONFIG[agent.type] || TYPE_CONFIG.coder
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
            <div className="font-mono text-[13px] text-[#f0f0f0] mb-1">{agent.id}</div>
            <div 
              className="text-[9px] px-1.5 py-0.5 rounded border inline-block"
              style={{
                borderColor: getAgentModel(agent.type).includes('deepseek') ? '#4f6ef733' : '#8b5cf633',
                backgroundColor: getAgentModel(agent.type).includes('deepseek') ? '#4f6ef711' : '#8b5cf611',
                color: getAgentModel(agent.type).includes('deepseek') ? '#4f6ef7' : '#8b5cf6'
              }}
            >
              {getModelDisplayName(getAgentModel(agent.type))}
            </div>
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
