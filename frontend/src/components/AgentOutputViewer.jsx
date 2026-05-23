import { useEffect, useState } from 'react'
import { FileCode2, Copy, Check, Loader2 } from 'lucide-react'
import useTaskStore from '../store/taskStore.js'

function AgentOutputViewer({ taskId }) {
  const [outputData, setOutputData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState('raw') // 'raw', 'coder', 'tester'
  const { fetchAgentOutput } = useTaskStore()

  useEffect(() => {
    let mounted = true
    if (!taskId) {
      setOutputData(null)
      setLoading(false)
      return
    }
    
    setLoading(true)
    const loadOutput = async () => {
      const data = await fetchAgentOutput(taskId)
      if (mounted) {
        setOutputData(data)
        if (data?.agent_output?.coder) setActiveTab('coder')
        else setActiveTab('raw')
        setLoading(false)
      }
    }
    loadOutput()
    const interval = setInterval(loadOutput, 5000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [taskId, fetchAgentOutput])

  if (!taskId) {
    return (
      <div className="bg-[#111111] border border-[#2a2a2a] rounded-xl h-full flex flex-col items-center justify-center text-[#555]">
        <FileCode2 size={48} className="mb-4 opacity-20" />
        <p className="text-[14px]">Select a task from the DAG to view output</p>
      </div>
    )
  }

  if (loading && !outputData) {
    return (
      <div className="bg-[#111111] border border-[#2a2a2a] rounded-xl h-full flex items-center justify-center">
        <Loader2 size={24} className="text-[#4f6ef7] animate-spin" />
      </div>
    )
  }

  if (!outputData) return null

  const tabs = ['raw', ...Object.keys(outputData.agent_output || {})]

  const getContentToRender = () => {
    if (activeTab === 'raw') return JSON.stringify(outputData.output_data, null, 2)
    const agentOut = outputData.agent_output[activeTab]
    if (agentOut?.output?.code) return agentOut.output.code
    if (agentOut?.fixed_code) return agentOut.fixed_code
    return JSON.stringify(agentOut, null, 2)
  }

  const content = getContentToRender()

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-[#111111] border border-[#2a2a2a] rounded-xl h-full flex flex-col overflow-hidden">
      <div className="px-4 py-2 border-b border-[#2a2a2a] flex justify-between items-center bg-[#0a0a0a]">
        <div className="flex gap-2">
          {tabs.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`text-[10px] uppercase tracking-widest px-3 py-1.5 rounded-md transition-colors ${
                activeTab === tab 
                  ? 'bg-[#2a2a2a] text-[#f0f0f0]' 
                  : 'text-[#888888] hover:text-[#f0f0f0]'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
        <button 
          onClick={handleCopy}
          className="text-[#888888] hover:text-[#f0f0f0] transition-colors p-1"
          title="Copy output"
        >
          {copied ? <Check size={16} className="text-[#22c55e]" /> : <Copy size={16} />}
        </button>
      </div>
      <div className="flex-1 overflow-auto bg-[#0a0a0a] p-4">
        <pre className="font-mono text-[12px] text-[#f0f0f0] leading-relaxed">
          <code>{content || 'No output data available yet...'}</code>
        </pre>
      </div>
    </div>
  )
}

export default AgentOutputViewer
