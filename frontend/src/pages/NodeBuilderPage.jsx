import { useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import ReactFlow, {
  Background,
  Controls,
  Handle,
  Position,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from 'reactflow'
import {
  Bell,
  ChevronDown,
  Code2,
  Eye,
  Settings,
  SlidersHorizontal,
} from 'lucide-react'
import { useParams } from 'react-router-dom'
import useLogStore from '../store/logStore.js'
import NodeDetailPanel from '../components/NodeDetailPanel.jsx'

const CronTriggerNode = ({ data }) => (
  <div className="w-[180px] bg-[#1a1a1a]/80 border border-[#2a2a2a] rounded-xl p-4 relative">
    <div className="flex items-center gap-3 mb-2">
      <div className="w-8 h-8 rounded-full bg-[#111111] border border-[#2a2a2a] flex items-center justify-center">
        <Eye size={16} className="text-[#4f6ef7]" />
      </div>
      <div>
        <h3 className="text-[12px] text-[#f0f0f0]">{data.title}</h3>
        <p className="text-[10px] font-mono text-[#888888]">{data.schedule}</p>
      </div>
    </div>
    <div className="flex justify-between items-center mt-3 pt-3 border-t border-[#2a2a2a]">
      <span
        className={`px-2 py-0.5 rounded text-[10px] uppercase tracking-widest ${
          data.status === 'Success'
            ? 'bg-[#22c55e]/20 text-[#22c55e]'
            : 'bg-[#ef4444]/20 text-[#ef4444]'
        }`}
      >
        {data.status}
      </span>
      <span className="text-[10px] font-mono text-[#888888]">{data.latency}</span>
    </div>
    <Handle
      type="source"
      position={Position.Right}
      className="!w-2 !h-2 !bg-[#f0f0f0] !border-none"
    />
  </div>
)

const DataProcessorNode = ({ data }) => (
  <div className="w-[300px] bg-[#1a1a1a]/90 border border-[#2a2a2a] rounded-xl p-5">
    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-white to-gray-400 rounded-t-xl opacity-80" />
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-[#2a2a2a] flex items-center justify-center border border-[#2a2a2a]">
          <Code2 size={18} className="text-[#4f6ef7]" />
        </div>
        <div>
          <h3 className="text-[16px] text-[#f0f0f0]">{data.title}</h3>
          <p className="text-[10px] font-mono text-[#888888]">ID: {data.nodeId}</p>
        </div>
      </div>
      <ChevronDown size={16} className="text-[#888888]" />
    </div>
    <div className="space-y-2 mb-4">
      <div className="flex justify-between text-[12px] font-mono">
        <span className="text-[#888888]">Tokens In:</span>
        <span className="text-[#f0f0f0]">{data.tokensIn}</span>
      </div>
      <div className="flex justify-between text-[12px] font-mono">
        <span className="text-[#888888]">Tokens Out:</span>
        <span className="text-[#f0f0f0]">{data.tokensOut}</span>
      </div>
    </div>
    <div className="space-y-2 mb-4">
      {data.statusTags.map((tag) => (
        <span
          key={tag.label}
          className={`inline-flex px-2 py-1 rounded text-[10px] uppercase tracking-widest border ${tag.className}`}
        >
          {tag.label}
        </span>
      ))}
    </div>
    <div className="bg-[#0f0f0f] p-3 rounded-lg border border-[#2a2a2a]">
      <p className="font-mono text-[11px] text-[#888888] line-clamp-2">
        {data.log}
      </p>
    </div>
    <div className="flex justify-between items-center mt-4 pt-4 border-t border-[#2a2a2a]">
      <span className="px-2 py-1 rounded text-[10px] uppercase tracking-widest bg-[#2a2a2a] text-[#f0f0f0]">
        {data.statusLabel}
      </span>
      <span className="text-[10px] font-mono text-[#888888]">{data.statusDetail}</span>
    </div>
    <Handle
      type="target"
      position={Position.Left}
      className="!w-2 !h-2 !bg-[#f0f0f0] !border-none"
    />
  </div>
)

const nodeTypes = {
  cronTrigger: CronTriggerNode,
  dataProcessor: DataProcessorNode,
}

function NodeBuilderPage() {
  const { id } = useParams()
  const { logs } = useLogStore()
  const [selectedNode, setSelectedNode] = useState(null)

  const initialNodes = useMemo(
    () => [
      {
        id: 'cron-1',
        type: 'cronTrigger',
        position: { x: 80, y: 160 },
        data: {
          title: 'Data Ingestion',
          schedule: 'Cron: 0 * * * *',
          status: 'Success',
          latency: '1.2s',
          label: 'Data Ingestion',
        },
      },
      {
        id: 'processor-1',
        type: 'dataProcessor',
        position: { x: 520, y: 260 },
        data: {
          title: 'Data Processor',
          nodeId: 'AGT-882',
          tokensIn: '4,092',
          tokensOut: '1,204',
          statusLabel: 'Running',
          statusDetail: 'Processing...',
          log: '> Processed 500 rows. Extracted key entities successfully.',
          statusTags: [
            { label: 'Running', className: 'bg-[#0f1a3a] text-[#4f6ef7] border-[#4f6ef7]' },
            { label: 'TypeErr: b...', className: 'bg-[#2a1010] text-[#ef4444] border-[#ef4444]' },
            { label: 'Failed', className: 'bg-[#2a1010] text-[#ef4444] border-[#ef4444]' },
          ],
          label: 'Data Processor',
        },
      },
    ],
    [],
  )

  const initialEdges = useMemo(
    () => [
      {
        id: 'edge-1',
        source: 'cron-1',
        target: 'processor-1',
        type: 'bezier',
        style: { stroke: '#f0f0f0' },
      },
    ],
    [],
  )

  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  const onNodeClick = (_, node) => {
    setSelectedNode(node)
  }

  const panelLogs = logs.filter((entry) => entry.nodeId === selectedNode?.id).slice(-5)
  const panelOpen = Boolean(selectedNode)

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="h-[calc(100vh-64px)] flex flex-col"
    >
      <header className="bg-[#0a0a0a]/70 border-b border-[#2a2a2a] flex items-center justify-between px-6 h-16 sticky top-0 z-20">
        <div className="flex items-center gap-6">
          <span className="text-[18px] font-semibold">Sync</span>
          <nav className="hidden md:flex items-center gap-6">
            {['Nodes', 'Variables', 'API'].map((tab) => (
              <button
                key={tab}
                type="button"
                className={`text-[12px] uppercase tracking-widest ${
                  tab === 'Variables'
                    ? 'text-[#f0f0f0] border-b-2 border-[#4f6ef7] pb-1'
                    : 'text-[#888888] hover:text-[#f0f0f0]'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <button className="p-2 rounded-full text-[#888888] hover:text-[#f0f0f0] hover:bg-white/5">
            <Bell size={16} />
          </button>
          <button className="p-2 rounded-full text-[#888888] hover:text-[#f0f0f0] hover:bg-white/5">
            <SlidersHorizontal size={16} />
          </button>
          <button className="p-2 rounded-full text-[#888888] hover:text-[#f0f0f0] hover:bg-white/5">
            <Settings size={16} />
          </button>
          <div className="w-8 h-8 rounded-full border border-[#2a2a2a] bg-[#1a1a1a]" />
        </div>
      </header>

      <div className="flex-1 flex relative bg-[#0a0a0a]">
        <div
          className={`flex-1 relative ${panelOpen ? 'pr-[280px]' : ''}`}
          style={{
            backgroundImage: 'radial-gradient(circle, #2a2a2a 1px, transparent 1px)',
            backgroundSize: '24px 24px',
          }}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            nodesDraggable
            onNodeClick={onNodeClick}
            fitView
            className="rf-dark"
          >
            <Background gap={24} size={1} color="#2a2a2a" />
            <Controls showInteractive={false} />
          </ReactFlow>

          <CanvasControls />
        </div>

        <NodeDetailPanel
          node={selectedNode}
          logs={panelLogs}
          onClose={() => setSelectedNode(null)}
        />
      </div>
    </motion.div>
  )
}

function CanvasControls() {
  const { zoomIn, zoomOut, fitView } = useReactFlow()

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2 bg-[#1a1a1a] border border-[#2a2a2a] rounded-full px-3 py-2 z-20">
      <button
        type="button"
        className="w-8 h-8 rounded-full bg-[#111111] text-[#f0f0f0] hover:bg-[#2a2a2a]"
        onClick={() => zoomIn()}
      >
        +
      </button>
      <button
        type="button"
        className="w-8 h-8 rounded-full bg-[#111111] text-[#f0f0f0] hover:bg-[#2a2a2a]"
        onClick={() => zoomOut()}
      >
        -
      </button>
      <button
        type="button"
        className="w-8 h-8 rounded-full bg-[#111111] text-[#f0f0f0] hover:bg-[#2a2a2a]"
        onClick={() => fitView()}
      >
        []
      </button>
    </div>
  )
}

export default NodeBuilderPage
