import { useEffect, useMemo, useRef } from 'react'
import { Download, Filter } from 'lucide-react'
import { motion } from 'framer-motion'
import useLogStore from '../store/logStore.js'

const LEVEL_STYLES = {
  info: 'text-[#888888]',
  debug: 'text-[#4f6ef7]',
  warning: 'text-[#f59e0b]',
  error: 'text-[#ef4444]',
}

const AGENT_COLORS = {
  CODER: '#4f6ef7',
  TESTER: '#8b5cf6',
  DEBUGGER: '#f59e0b',
  REVIEWER: '#22c55e',
  PLANNER: '#06b6d4',
}

function getAgentColor(message) {
  const match = message.match(/\[([A-Z]+)\]/)
  if (match) return AGENT_COLORS[match[1]] ?? '#888888'
  return '#888888'
}

function ExecutionLogPanel({ agentId }) {
  const { logs } = useLogStore()
  const logEndRef = useRef(null)

  const filteredLogs = useMemo(() => {
    if (!agentId) return logs
    return logs.filter((entry) => entry.task_id === agentId || entry.workflow_id === agentId)
  }, [logs, agentId])

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [filteredLogs.length])

  return (
    <div className="bg-[#1a1a1a]/70 border border-[#2a2a2a] rounded-xl flex flex-col overflow-hidden">
      <div className="flex justify-between items-center px-4 py-3 border-b border-[#2a2a2a] bg-[#111111]/50">
        <h3 className="text-[12px] uppercase tracking-widest text-[#f0f0f0] flex items-center gap-2">
          Execution Log
        </h3>
        <div className="flex gap-2 text-[#888888]">
          <button className="hover:text-[#f0f0f0]" type="button">
            <Filter size={16} />
          </button>
          <button className="hover:text-[#f0f0f0]" type="button">
            <Download size={16} />
          </button>
        </div>
      </div>
      <div className="flex-1 bg-[#0f0f0f] p-4 overflow-y-auto font-mono text-[13px] space-y-1">
        {filteredLogs.map((entry) => (
          <motion.div
            key={entry.id}
            initial={{ x: -8, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="text-[#888888]"
          >
            <span className="text-[#888888]">[{new Date(entry.created_at).toLocaleTimeString()}]</span>{' '}
            <span className={LEVEL_STYLES[entry.level] || 'text-[#f0f0f0]'}>
              {entry.level}
            </span>
            : <span style={{ color: getAgentColor(entry.message) }}>{entry.message}</span>
          </motion.div>
        ))}
        <div ref={logEndRef} />
      </div>
    </div>
  )
}

export default ExecutionLogPanel
