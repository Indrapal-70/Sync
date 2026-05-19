import { motion } from 'framer-motion'
import { useEffect } from 'react'
import useModelStore from '../store/modelStore'
import { Cpu, Code2, Shield, Bug, Bot, Route } from 'lucide-react'

const AGENT_ICONS = {
  coder: Code2,
  tester: Shield,
  debugger: Bug,
  reviewer: Code2,
  planner: Bot,
}

function ProjectSettingsPage() {
  const { config, fetchConfig } = useModelStore()

  useEffect(() => {
    fetchConfig()
  }, [fetchConfig])

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="p-8 text-[#888888] max-w-4xl mx-auto"
    >
      <h1 className="text-[28px] md:text-[32px] font-semibold text-[#f0f0f0] mb-8">Settings</h1>
      
      <section className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <Route className="text-[#4f6ef7]" size={24} />
          <h2 className="text-lg font-semibold text-[#f0f0f0]">Model Routing</h2>
        </div>
        
        <p className="text-sm mb-6 max-w-2xl">
          Configure which local AI model handles each agent's tasks. Models are orchestrated via Ollama.
        </p>

        {!config ? (
          <div className="animate-pulse flex space-x-4">
            <div className="flex-1 space-y-4 py-1">
              <div className="h-4 bg-[#2a2a2a] rounded w-3/4"></div>
              <div className="space-y-2">
                <div className="h-4 bg-[#2a2a2a] rounded"></div>
                <div className="h-4 bg-[#2a2a2a] rounded w-5/6"></div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4 font-semibold text-[10px] uppercase tracking-widest text-[#555555] mb-2 px-2">
              <div>Agent Role</div>
              <div className="col-span-2">Assigned Model</div>
            </div>
            
            {Object.entries(config.routing || {}).map(([agent, model]) => {
              const Icon = AGENT_ICONS[agent] || Bot
              const isDeepseek = model.includes('deepseek')
              return (
                <div key={agent} className="grid grid-cols-3 gap-4 bg-[#111111] p-3 rounded-lg border border-[#2a2a2a] items-center">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-[#2a2a2a] rounded border border-[#3a3a3a]">
                      <Icon size={16} className="text-[#888888]" />
                    </div>
                    <span className="text-[#f0f0f0] uppercase tracking-widest text-[11px] font-semibold">{agent}</span>
                  </div>
                  
                  <div className="col-span-2 flex items-center">
                    <select 
                      disabled 
                      className="w-full bg-[#1a1a1a] border border-[#2a2a2a] text-[#888888] rounded p-2 text-sm appearance-none cursor-not-allowed font-mono"
                      value={model}
                    >
                      <option value={model}>{model}</option>
                    </select>
                    
                    <div className="ml-3">
                      <Cpu size={16} className={isDeepseek ? "text-[#4f6ef7]" : "text-[#8b5cf6]"} />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>
    </motion.div>
  )
}

export default ProjectSettingsPage
