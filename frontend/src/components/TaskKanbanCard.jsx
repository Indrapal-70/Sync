import { AlertTriangle, BarChart2, Bug, Code2, FlaskConical } from 'lucide-react'

const AGENT_COLORS = {
  programmer: 'bg-[#4f6ef7] text-[#0a0a0a]',
  tester: 'bg-[#a855f7] text-[#0a0a0a]',
  debugger: 'bg-[#f59e0b] text-[#0a0a0a]',
  researcher: 'bg-[#14b8a6] text-[#0a0a0a]',
  writer: 'bg-[#f97316] text-[#0a0a0a]',
}

const AGENT_ICONS = {
  programmer: Code2,
  tester: FlaskConical,
  debugger: Bug,
  researcher: Bug,
  writer: Code2,
}

function TaskKanbanCard({ task }) {
  const badgeStyle = AGENT_COLORS[task.agent_name] || AGENT_COLORS.programmer
  const Icon = AGENT_ICONS[task.agent_name] || Code2

  return (
    <div className="bg-[#1a1a1a]/70 border border-[#2a2a2a] rounded-lg p-4 hover:border-[#4f6ef7]/40 transition-colors cursor-default">
      <div className="flex justify-between items-start mb-3">
        <span className={`px-2 py-1 rounded text-[10px] uppercase tracking-widest ${badgeStyle}`}>
          {task.agent_name || 'unassigned'}
        </span>
        <div className="flex items-center gap-2 text-[#888888]">
          {task.status === 'failed' && <AlertTriangle size={16} className="text-[#ef4444]" />}
          <BarChart2 size={16} />
        </div>
      </div>
      <h4 className="text-[16px] font-semibold text-[#f0f0f0] mb-2">
        {task.name}
      </h4>
      <p className="text-[13px] text-[#888888] mb-4 line-clamp-2">
        {task.description}
      </p>
      {task.status === 'running' && typeof task.progress === 'number' && (
        <div className="mb-4">
          <div className="flex justify-between text-[12px] text-[#888888] mb-1">
            <span>Progress</span>
            <span>{task.progress}%</span>
          </div>
          <div className="w-full h-1 bg-[#2a2a2a] rounded-full overflow-hidden">
            <div className="h-full bg-[#f0f0f0]" style={{ width: `${task.progress}%` }} />
          </div>
        </div>
      )}
      {task.status === 'testing' && typeof task.coverage === 'number' && (
        <div className="mb-4">
          <div className="flex justify-between text-[12px] text-[#888888] mb-1">
            <span>Test Coverage</span>
            <span>{task.coverage}%</span>
          </div>
          <div className="w-full h-1 bg-[#2a2a2a] rounded-full overflow-hidden">
            <div className="h-full bg-[#f0f0f0]" style={{ width: `${task.coverage}%` }} />
          </div>
        </div>
      )}
      <div className="flex justify-between items-end pt-3 border-t border-[#2a2a2a]">
        <div className="text-[12px] font-mono text-[#555555]">{task.id}</div>
        <div className="w-6 h-6 rounded-full bg-[#111111] border border-[#2a2a2a] flex items-center justify-center">
          <Icon size={14} className="text-[#f0f0f0]" />
        </div>
      </div>
    </div>
  )
}

export default TaskKanbanCard
