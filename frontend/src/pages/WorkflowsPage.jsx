import { motion } from 'framer-motion'
import { useMemo } from 'react'
import { ChevronRight, Zap } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import WorkflowDAG from '../components/WorkflowDAG.jsx'
import useWorkflowStore from '../store/workflowStore.js'

function WorkflowsPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { workflows } = useWorkflowStore()

  const workflowName = useMemo(() => {
    const workflow = workflows.find((item) => item.id === id)
    return workflow?.name || 'Task Divider Bot'
  }, [workflows, id])

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col h-[calc(100vh-64px)]"
    >
      <header className="h-16 px-6 flex items-center justify-between border-b border-[#2a2a2a] bg-[#0a0a0a]/90 backdrop-blur-sm">
        <div className="flex items-center gap-2 text-[#888888] text-[10px] uppercase tracking-widest">
          <span>Workflows</span>
          <ChevronRight size={14} />
          <span>{workflowName}</span>
          <ChevronRight size={14} />
          <span className="text-[#f0f0f0]">Task Deconstruction</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 border border-[#2a2a2a] px-3 py-1.5 rounded-full">
            <span className="w-2 h-2 rounded-full bg-[#22c55e] status-pulse" />
            <span className="text-[10px] uppercase tracking-widest text-[#22c55e]">
              Deconstruction Active
            </span>
          </div>
          <button
            className="text-[10px] uppercase tracking-widest px-3 py-2 rounded border border-[#2a2a2a] text-[#f0f0f0] hover:bg-[#1a1a1a] transition-colors flex items-center gap-2"
            type="button"
            onClick={() => navigate(`/workflows/${id}/builder`)}
          >
            <Zap size={14} /> Open Builder
          </button>
        </div>
      </header>
      <div className="flex-1 bg-[#0a0a0a]">
        <WorkflowDAG />
      </div>
    </motion.div>
  )
}

export default WorkflowsPage
