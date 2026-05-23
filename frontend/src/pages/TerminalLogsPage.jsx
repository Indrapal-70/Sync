import { motion } from 'framer-motion'
import { useMemo, useState, useRef, useEffect } from 'react'
import { Search, Filter, Terminal, Trash2, Pause, Play, Download } from 'lucide-react'
import useLogStore from '../store/logStore.js'

function TerminalLogsPage() {
  const { logs, clearLogs } = useLogStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [levelFilter, setLevelFilter] = useState('all') // all, info, warning, error, debug
  const [agentFilter, setAgentFilter] = useState('all') // all, coder, tester, system, etc.
  const [autoScroll, setAutoScroll] = useState(true)
  
  const bottomRef = useRef(null)

  // Use logs but reverse them so newest are at the bottom
  const orderedLogs = useMemo(() => [...logs].reverse(), [logs])

  const filteredLogs = useMemo(() => {
    return orderedLogs.filter(log => {
      if (levelFilter !== 'all' && log.level !== levelFilter) return false
      
      if (agentFilter !== 'all') {
        const agName = log.agent_name?.toLowerCase() || 'system'
        if (agName !== agentFilter) return false
      }

      if (searchTerm) {
        const lowerSearch = searchTerm.toLowerCase()
        return (
          log.message?.toLowerCase().includes(lowerSearch) || 
          log.agent_name?.toLowerCase().includes(lowerSearch)
        )
      }
      return true
    })
  }, [orderedLogs, searchTerm, levelFilter, agentFilter])

  // Extract unique agents
  const agents = useMemo(() => {
    const s = new Set(logs.map(l => l.agent_name?.toLowerCase() || 'system'))
    return ['all', ...Array.from(s)]
  }, [logs])

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [filteredLogs, autoScroll])

  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target
    // If we scroll up, disable auto-scroll
    if (scrollHeight - scrollTop - clientHeight > 50) {
      setAutoScroll(false)
    } else {
      setAutoScroll(true)
    }
  }

  const exportLogs = () => {
    const text = filteredLogs.map(l => `[${new Date(l.created_at).toISOString()}] ${l.level.toUpperCase()} [${l.agent_name || 'SYSTEM'}] ${l.message}`).join('\n')
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `sync-logs-${new Date().toISOString()}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="p-4 md:p-8 flex flex-col h-[calc(100vh-64px)]"
    >
      <div className="bg-[#111111] border border-[#2a2a2a] rounded-xl flex flex-col h-full overflow-hidden shadow-2xl">
        
        {/* Toolbar */}
        <div className="px-4 py-3 border-b border-[#2a2a2a] bg-[#0a0a0a] flex flex-wrap gap-4 items-center justify-between shrink-0">
          <div className="flex items-center gap-2 text-[#f0f0f0]">
            <Terminal size={18} className="text-[#4f6ef7]" />
            <h2 className="text-[14px] font-semibold tracking-wide">Live Logs</h2>
            <span className="ml-2 text-[10px] bg-[#2a2a2a] text-[#888888] px-2 py-0.5 rounded-full">
              {filteredLogs.length} events
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#555]" />
              <input 
                type="text" 
                placeholder="Search logs..." 
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg pl-8 pr-4 py-1.5 text-[12px] text-[#f0f0f0] focus:border-[#4f6ef7] focus:outline-none w-48 transition-colors"
              />
            </div>

            {/* Level Filter */}
            <div className="flex items-center gap-2">
              <Filter size={14} className="text-[#555]" />
              <select 
                value={levelFilter}
                onChange={e => setLevelFilter(e.target.value)}
                className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-2 py-1.5 text-[12px] text-[#f0f0f0] focus:border-[#4f6ef7] focus:outline-none cursor-pointer"
              >
                <option value="all">All Levels</option>
                <option value="info">Info</option>
                <option value="debug">Debug</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
              </select>
            </div>

            {/* Agent Filter */}
            <select 
              value={agentFilter}
              onChange={e => setAgentFilter(e.target.value)}
              className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-2 py-1.5 text-[12px] text-[#f0f0f0] focus:border-[#4f6ef7] focus:outline-none cursor-pointer"
            >
              {agents.map(ag => (
                <option key={ag} value={ag}>
                  {ag === 'all' ? 'All Agents' : ag.toUpperCase()}
                </option>
              ))}
            </select>

            <div className="w-px h-6 bg-[#2a2a2a] mx-1" />

            {/* Actions */}
            <button 
              onClick={() => setAutoScroll(!autoScroll)}
              className={`p-1.5 rounded-md border ${autoScroll ? 'bg-[#4f6ef7]/10 border-[#4f6ef7]/30 text-[#4f6ef7]' : 'bg-[#1a1a1a] border-[#2a2a2a] text-[#888888] hover:text-[#f0f0f0]'}`}
              title={autoScroll ? 'Pause auto-scroll' : 'Resume auto-scroll'}
            >
              {autoScroll ? <Pause size={14} /> : <Play size={14} />}
            </button>
            <button 
              onClick={exportLogs}
              className="p-1.5 rounded-md bg-[#1a1a1a] border border-[#2a2a2a] text-[#888888] hover:text-[#f0f0f0]"
              title="Export Logs"
            >
              <Download size={14} />
            </button>
            <button 
              onClick={clearLogs}
              className="p-1.5 rounded-md bg-[#1a1a1a] border border-[#2a2a2a] text-[#ef4444] hover:bg-[#ef4444]/10"
              title="Clear Logs"
            >
              <Trash2 size={14} />
            </button>
          </div>
        </div>

        {/* Log Viewer */}
        <div 
          className="flex-1 overflow-y-auto p-4 font-mono text-[12px] space-y-1.5 bg-[#0a0a0a]"
          onScroll={handleScroll}
        >
          {filteredLogs.map((entry) => (
            <div key={entry.id} className="flex gap-3 hover:bg-[#1a1a1a] px-2 py-1 rounded transition-colors group">
              <span className="text-[#555555] shrink-0 select-none">
                {new Date(entry.created_at).toLocaleTimeString()}
              </span>
              <span className={`shrink-0 w-16 uppercase tracking-wider text-[10px] font-bold mt-0.5 ${
                entry.level === 'error' ? 'text-[#ef4444]' : 
                entry.level === 'warning' ? 'text-[#f59e0b]' : 
                entry.level === 'debug' ? 'text-[#a855f7]' : 
                'text-[#4f6ef7]'
              }`}>
                {entry.level}
              </span>
              <span className="shrink-0 w-24 text-[10px] uppercase text-[#888] mt-0.5 select-none overflow-hidden text-ellipsis whitespace-nowrap">
                [{entry.agent_name || 'SYSTEM'}]
              </span>
              <span className={`flex-1 break-words ${entry.level === 'error' ? 'text-[#ef4444]' : 'text-[#d4d4d4]'}`}>
                {entry.message}
              </span>
            </div>
          ))}
          {filteredLogs.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-[#555555] space-y-4">
              <Terminal size={48} className="opacity-20" />
              <p>No logs match the current filters.</p>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </motion.div>
  )
}

export default TerminalLogsPage
