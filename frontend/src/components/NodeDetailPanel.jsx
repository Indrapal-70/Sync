import { ChevronDown, X, Cpu } from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'

const getModelDisplayName = (fullName) => {
  if (!fullName) return 'unknown'
  if (fullName.includes('deepseek')) return 'deepseek-coder'
  if (fullName.includes('mistral')) return 'mistral'
  return fullName.split(':')[0]
}

function NodeDetailPanel({ node, logs, onClose }) {
  const agentOutputs = node?.data?.agentOutput || {}
  const modelSummary = node?.data?.modelSummary || {}

  return (
    <AnimatePresence>
      {node && (
        <motion.aside
          initial={{ x: 320, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 320, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="absolute top-0 right-0 h-full w-full md:w-[280px] bg-[#1a1a1a]/95 border-l border-[#2a2a2a] shadow-2xl flex flex-col z-30"
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
                  {node?.data?.agent || 'Agent'}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] uppercase tracking-widest bg-[#2a2a2a] text-[#888888]">
                  {node?.data?.statusLabel || 'Status'}
                </span>
              </div>
              <h3 className="text-[18px] font-semibold text-[#f0f0f0]">{node?.data?.label}</h3>
              <p className="text-[12px] text-[#888888] mt-1">
                ID: {node?.id}
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
                      <span className="text-[#555555]">
                        {new Date(entry.created_at).toLocaleTimeString()}
                      </span>{' '}
                      [{entry.level}] {entry.message}
                    </div>
                  ))}
                </div>
              </details>

              {/* Agent Outputs */}
              {Object.entries(agentOutputs).map(([agentName, output]) => {
                const modelUsed = output?.model_used
                return (
                  <details key={agentName} className="group bg-[#111111] rounded-lg border border-[#2a2a2a] overflow-hidden">
                    <summary className="flex items-center justify-between p-3 cursor-pointer bg-[#202020]/40 hover:bg-[#202020]/70 transition-colors">
                      <div className="flex flex-col">
                        <span className="text-[12px] uppercase tracking-widest text-[#f0f0f0]">
                          {agentName} Output
                        </span>
                        {modelUsed && (
                          <span className="text-[9px] text-[#888888] uppercase tracking-widest mt-0.5 flex items-center gap-1">
                            <Cpu size={10} /> via {getModelDisplayName(modelUsed)}
                          </span>
                        )}
                      </div>
                      <ChevronDown size={16} className="text-[#888888] group-open:rotate-180 transition-transform" />
                    </summary>
                    <div className="p-3 border-t border-[#2a2a2a] bg-[#0f0f0f] font-mono text-[11px] space-y-1">
                      <pre className="text-[#888888] whitespace-pre-wrap overflow-x-auto text-[10px]">
                        {JSON.stringify(output, null, 2)}
                      </pre>
                    </div>
                  </details>
                )
              })}
            </div>

            {/* Model Summary */}
            {Object.keys(modelSummary).length > 0 && (
              <div className="mt-4 pt-4 border-t border-[#2a2a2a]">
                <h4 className="text-[10px] uppercase tracking-widest text-[#888888] mb-3">
                  Task Model Summary
                </h4>
                <div className="space-y-2">
                  {Object.entries(modelSummary).map(([modelName, count]) => (
                    <div key={modelName} className="flex justify-between items-center bg-[#111111] p-2 rounded border border-[#2a2a2a]">
                      <span className="text-[11px] text-[#f0f0f0] flex items-center gap-2">
                        <Cpu size={12} className={modelName.includes('deepseek') ? 'text-[#4f6ef7]' : 'text-[#8b5cf6]'} />
                        {getModelDisplayName(modelName)}
                      </span>
                      <span className="text-[10px] font-mono text-[#888888]">
                        {count} {count === 1 ? 'call' : 'calls'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
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
