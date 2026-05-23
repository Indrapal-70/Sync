import { useEffect, useState } from 'react'
import { CheckCircle2, Clock, Play, AlertCircle, RefreshCw, XCircle } from 'lucide-react'
import useWorkflowStore from '../store/workflowStore.js'

function getEventIcon(level, stage) {
  if (level === 'error') return <XCircle size={14} className="text-[#ef4444]" />
  if (level === 'warning') return <AlertCircle size={14} className="text-[#f59e0b]" />
  if (stage === 'done') return <CheckCircle2 size={14} className="text-[#22c55e]" />
  if (stage === 'planning' || stage === 'coding' || stage === 'testing') return <Play size={14} className="text-[#4f6ef7]" />
  return <Clock size={14} className="text-[#888888]" />
}

function TaskTimeline({ workflowId }) {
  const [timeline, setTimeline] = useState([])
  const [loading, setLoading] = useState(true)
  const { fetchTimeline } = useWorkflowStore()

  useEffect(() => {
    let mounted = true
    const loadTimeline = async () => {
      const data = await fetchTimeline(workflowId)
      if (mounted) {
        setTimeline(data)
        setLoading(false)
      }
    }
    loadTimeline()
    const interval = setInterval(loadTimeline, 5000) // Poll every 5s for now
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [workflowId, fetchTimeline])

  if (loading) return <div className="p-4 text-[12px] text-[#888888]">Loading timeline...</div>

  return (
    <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl overflow-hidden flex flex-col h-full">
      <div className="px-4 py-3 border-b border-[#2a2a2a] flex justify-between items-center bg-[#111111]">
        <h3 className="text-[12px] uppercase tracking-widest text-[#f0f0f0]">Event Timeline</h3>
        <span className="text-[10px] bg-[#2a2a2a] text-[#888888] px-2 py-0.5 rounded">{timeline.length} events</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {timeline.map((event, i) => (
          <div key={event.id} className="relative flex gap-4">
            {i !== timeline.length - 1 && (
              <div className="absolute left-3 top-6 bottom-[-1rem] w-px bg-[#2a2a2a]" />
            )}
            <div className="relative z-10 w-6 h-6 rounded-full bg-[#111111] border border-[#2a2a2a] flex items-center justify-center shrink-0">
              {getEventIcon(event.level, event.pipeline_stage)}
            </div>
            <div className="flex-1 pb-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[12px] font-semibold text-[#f0f0f0]">
                  {event.agent_name ? event.agent_name.toUpperCase() : 'SYSTEM'}
                </span>
                <span className="text-[10px] text-[#555555]">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <p className={`text-[12px] font-mono ${event.level === 'error' ? 'text-[#ef4444]' : 'text-[#888888]'}`}>
                {event.message}
              </p>
              {event.pipeline_stage && (
                <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 bg-[#2a2a2a] text-[#888888] rounded">
                  {event.pipeline_stage}
                </span>
              )}
            </div>
          </div>
        ))}
        {timeline.length === 0 && <div className="text-[12px] text-[#555] text-center mt-8">No events yet.</div>}
      </div>
    </div>
  )
}

export default TaskTimeline
