import { ChevronDown, X } from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'

function NodeDetailPanel({ node, logs, onClose }) {
  return (
    <AnimatePresence>
      {node && (
        <motion.aside
          initial={{ x: 320, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 320, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="absolute top-0 right-0 h-full w-full md:w-[320px] bg-[#1a1a1a]/95 border-l border-[#2a2a2a] shadow-2xl flex flex-col z-30"
        >
          <div className="p-4 border-b border-[#2a2a2a] flex justify-between items-center bg-[#202020]/60">
            <h2 className="text-[16px] font-semibold text-[#f0f0f0]">Node Details</h2>
            <button
              onClick={onClose}
              className="text-[#888888] hover:text-[#f0f0f0] p-1 rounded hover:bg-white/5"
              type="button"
            >
              <X size={16} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-5 space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 rounded text-[10px] uppercase tracking-widest bg-[#2a2a2a] text-[#f0f0f0] border border-[#2a2a2a]">
                  Programmer
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] uppercase tracking-widest bg-[#2a2a2a] text-[#888888]">
                  GPT-4-Turbo
                </span>
              </div>
              <h3 className="text-[18px] font-semibold text-[#f0f0f0]">{node?.data?.label}</h3>
              <p className="text-[12px] text-[#888888] mt-1">
                ID: {node?.id} | Started 2m ago
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-[#111111] p-3 rounded-lg border border-[#2a2a2a]">
                <p className="text-[12px] text-[#888888] mb-1">Latency</p>
                <p className="font-mono text-[16px] text-[#f0f0f0]">1.4s</p>
              </div>
              <div className="bg-[#111111] p-3 rounded-lg border border-[#2a2a2a]">
                <p className="text-[12px] text-[#888888] mb-1">Cost</p>
                <p className="font-mono text-[16px] text-[#f0f0f0]">$0.04</p>
              </div>
            </div>

            <div className="space-y-3">
              <details
                className="group bg-[#111111] rounded-lg border border-[#2a2a2a] overflow-hidden"
                open
              >
                <summary className="flex items-center justify-between p-3 cursor-pointer bg-[#202020]/40 hover:bg-[#202020]/70 transition-colors">
                  <span className="text-[12px] uppercase tracking-widest text-[#f0f0f0]">
                    System Prompt
                  </span>
                  <ChevronDown size={16} className="text-[#888888] group-open:rotate-180 transition-transform" />
                </summary>
                <div className="p-3 border-t border-[#2a2a2a] bg-[#0f0f0f]">
                  <p className="text-[11px] text-[#888888] leading-relaxed">
                    You are an expert data extraction agent. Read the provided unstructured text and output a valid JSON object matching the defined schema. Ignore extraneous conversational data.
                  </p>
                </div>
              </details>
              <details className="group bg-[#111111] rounded-lg border border-[#2a2a2a] overflow-hidden">
                <summary className="flex items-center justify-between p-3 cursor-pointer bg-[#202020]/40 hover:bg-[#202020]/70 transition-colors">
                  <span className="text-[12px] uppercase tracking-widest text-[#f0f0f0]">
                    Recent Logs
                  </span>
                  <ChevronDown size={16} className="text-[#888888] group-open:rotate-180 transition-transform" />
                </summary>
                <div className="p-3 border-t border-[#2a2a2a] bg-[#0f0f0f] font-mono text-[11px] space-y-1">
                  {logs.map((entry) => (
                    <div key={entry.id} className="text-[#888888]">
                      <span className="text-[#555555]">{entry.time}</span> [{entry.level}] {entry.message}
                    </div>
                  ))}
                </div>
              </details>
            </div>
          </div>
          <div className="p-4 border-t border-[#2a2a2a] bg-[#1a1a1a] flex gap-3">
            <button className="flex-1 bg-[#2a2a2a] text-[#f0f0f0] hover:bg-[#3a3a3a] text-[12px] uppercase tracking-widest py-2 rounded border border-[#2a2a2a]">
              Pause
            </button>
            <button className="flex-1 bg-transparent border border-[#ef4444] text-[#ef4444] hover:bg-[#2a1010] text-[12px] uppercase tracking-widest py-2 rounded">
              Terminate
            </button>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  )
}

export default NodeDetailPanel
