import { motion } from 'framer-motion'
import { useMemo } from 'react'
import useLogStore from '../store/logStore.js'

function TerminalLogsPage() {
  const { logs } = useLogStore()
  const ordered = useMemo(() => logs.slice(0, 200), [logs])

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="p-8 text-[#888888]"
    >
      <div className="bg-[#0f0f0f] border border-[#2a2a2a] rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-[#2a2a2a] text-[12px] uppercase tracking-widest text-[#f0f0f0]">
          Terminal Logs
        </div>
        <div className="p-4 font-mono text-[12px] space-y-1 max-h-[70vh] overflow-y-auto">
          {ordered.map((entry) => (
            <div key={entry.id} className="text-[#888888]">
              <span className="text-[#555555]">
                [{new Date(entry.created_at).toLocaleTimeString()}]
              </span>{' '}
              <span className={entry.level === 'error' ? 'text-[#ef4444]' : 'text-[#888888]'}>
                {entry.level}
              </span>{' '}
              {entry.message}
            </div>
          ))}
          {ordered.length === 0 && <div className="text-[#555555]">No logs yet.</div>}
        </div>
      </div>
    </motion.div>
  )
}

export default TerminalLogsPage
