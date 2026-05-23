import { motion } from 'framer-motion'
import { useEffect, useMemo, useState } from 'react'
import { ChevronRight, Play, Settings2, Trash2, Save, Activity, RefreshCw } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import WorkflowDAG from '../components/WorkflowDAG.jsx'
import TaskTimeline from '../components/TaskTimeline.jsx'
import AgentOutputViewer from '../components/AgentOutputViewer.jsx'
import useWorkflowStore from '../store/workflowStore.js'
import useTaskStore from '../store/taskStore.js'

function WorkflowsPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { 
    workflows, 
    fetchWorkflows, 
    executeWorkflow, 
    deleteWorkflow, 
    saveAsTemplate,
    fetchSummary 
  } = useWorkflowStore()
  const { tasks, fetchTasks } = useTaskStore()

  const [selectedTaskId, setSelectedTaskId] = useState(null)
  const [summary, setSummary] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    fetchWorkflows()
    fetchTasks(id)
  }, [fetchWorkflows, fetchTasks, id])

  useEffect(() => {
    let mounted = true
    const loadSummary = async () => {
      const data = await fetchSummary(id)
      if (mounted) setSummary(data)
    }
    loadSummary()
    const interval = setInterval(loadSummary, 5000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [id, fetchSummary])

  const workflow = useMemo(() => workflows.find((item) => item.id === id), [workflows, id])
  const workflowTasks = useMemo(
    () => tasks.filter((task) => task.workflow_id === id),
    [tasks, id],
  )

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this workflow?')) {
      setIsDeleting(true)
      await deleteWorkflow(id)
      navigate('/workflows')
    }
  }

  const handleSaveTemplate = async () => {
    setIsSaving(true)
    try {
      await saveAsTemplate(id)
      alert('Workflow saved as template successfully!')
    } catch (e) {
      alert('Failed to save template.')
    } finally {
      setIsSaving(false)
    }
  }

  if (!workflow) return <div className="p-8 text-[#888888]">Loading...</div>

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col h-[calc(100vh-64px)] overflow-hidden"
    >
      <header className="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between border-b border-[#2a2a2a] bg-[#0a0a0a]/90 backdrop-blur-sm shrink-0 gap-4">
        <div>
          <div className="flex items-center gap-2 text-[#888888] text-[10px] uppercase tracking-widest mb-2">
            <span>Workflows</span>
            <ChevronRight size={14} />
            <span className="text-[#f0f0f0]">{workflow.name}</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-[20px] font-semibold text-[#f0f0f0]">{workflow.name}</h1>
            <div className="flex items-center gap-2 border border-[#2a2a2a] px-3 py-1 rounded-full bg-[#111111]">
              <span className={`w-2 h-2 rounded-full ${workflow.status === 'completed' ? 'bg-[#22c55e]' : workflow.status === 'failed' ? 'bg-[#ef4444]' : 'bg-[#4f6ef7] animate-pulse'}`} />
              <span className="text-[10px] uppercase tracking-widest text-[#f0f0f0]">
                {workflow.status}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            className="text-[11px] uppercase tracking-widest px-4 py-2 rounded-lg border border-[#4f6ef7] text-[#4f6ef7] hover:bg-[#4f6ef7]/10 transition-colors flex items-center gap-2 font-medium"
            type="button"
            onClick={() => executeWorkflow(id)}
          >
            <Play size={14} /> Re-Execute
          </button>
          <button
            className="text-[11px] uppercase tracking-widest px-4 py-2 rounded-lg border border-[#2a2a2a] text-[#f0f0f0] hover:bg-[#1a1a1a] transition-colors flex items-center gap-2"
            type="button"
            onClick={handleSaveTemplate}
            disabled={isSaving}
          >
            {isSaving ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />} 
            Save Template
          </button>
          <button
            className="text-[11px] uppercase tracking-widest px-4 py-2 rounded-lg border border-[#ef4444]/30 text-[#ef4444] hover:bg-[#ef4444]/10 transition-colors flex items-center gap-2"
            type="button"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            <Trash2 size={14} /> Delete
          </button>
        </div>
      </header>

      {/* Summary Bar */}
      {summary && (
        <div className="px-6 py-3 border-b border-[#2a2a2a] bg-[#111111] flex flex-wrap gap-6 shrink-0 text-[12px]">
          <div className="flex items-center gap-2">
            <Activity size={14} className="text-[#888888]" />
            <span className="text-[#888888]">Duration:</span>
            <span className="text-[#f0f0f0] font-mono">{summary.duration_seconds}s</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[#888888]">Tasks:</span>
            <span className="text-[#f0f0f0] font-mono">{summary.completed_tasks} / {summary.total_tasks}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[#888888]">Failed:</span>
            <span className="text-[#ef4444] font-mono">{summary.failed_tasks}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[#888888]">Models Used:</span>
            <div className="flex gap-1">
              {summary.models_used.map(m => (
                <span key={m} className="px-1.5 py-0.5 bg-[#2a2a2a] rounded text-[10px] text-[#f0f0f0]">{m}</span>
              ))}
              {summary.models_used.length === 0 && <span className="text-[#555]">-</span>}
            </div>
          </div>
        </div>
      )}

      <div className="flex-1 flex overflow-hidden p-6 gap-6 bg-[#0a0a0a]">
        <div className="flex-1 flex flex-col min-w-0 gap-6">
          {/* Top Half: DAG */}
          <div className="flex-[3] border border-[#2a2a2a] rounded-xl overflow-hidden bg-[#111111]">
            <WorkflowDAG 
              workflow={workflow} 
              tasks={workflowTasks} 
              onTaskSelect={setSelectedTaskId} 
            />
          </div>
          
          {/* Bottom Half: Output Viewer */}
          <div className="flex-[2] min-h-0">
            <AgentOutputViewer taskId={selectedTaskId} />
          </div>
        </div>

        {/* Right Column: Timeline */}
        <div className="w-[340px] shrink-0 min-h-0">
          <TaskTimeline workflowId={id} />
        </div>
      </div>
    </motion.div>
  )
}

export default WorkflowsPage
