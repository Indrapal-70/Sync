import { useMemo } from 'react'
import ReactFlow, { Controls, Background } from 'reactflow'
import { Bug, Database, Shield, Split, Target } from 'lucide-react'

const PrimaryObjectiveNode = ({ data }) => (
  <div className="w-[480px] bg-[#1b1b1b] border border-[#4f6ef7] rounded-lg p-6 shadow-lg">
    <div className="flex justify-between items-start mb-4">
      <div className="flex items-center gap-2">
        <Target size={18} className="text-[#4f6ef7]" />
        <span className="text-[10px] uppercase tracking-widest text-[#888888]">
          Primary Objective
        </span>
      </div>
      <span className="text-[11px] font-mono text-[#888888]">ID: {data.id}</span>
    </div>
    <h3 className="text-[20px] text-[#f0f0f0] font-semibold mb-2">{data.title}</h3>
    <p className="text-[14px] text-[#888888] leading-relaxed">{data.description}</p>
  </div>
)

const DividerNode = () => (
  <div className="px-4 py-2 rounded-full bg-[#0f0f0f] border border-[#2a2a2a] flex items-center gap-2">
    <Split size={16} className="text-[#888888]" />
    <span className="text-[10px] uppercase tracking-widest text-[#888888]">
      Task Scheduler Divider
    </span>
  </div>
)

const SequenceNode = ({ data }) => {
  const statusStyles = {
    passed: 'border-[#4f6ef7] text-[#4f6ef7] shadow-[0_0_24px_rgba(79,110,247,0.15)]',
    failed: 'border-[#ef4444] text-[#ef4444]',
    pending: 'border-[#2a2a2a] text-[#888888] opacity-60',
  }

  return (
    <div
      className={`w-[260px] bg-[#131313] border rounded-lg p-4 ${
        statusStyles[data.status]
      }`}
    >
      <div className="flex justify-between items-center mb-3">
        <span
          className={`text-[10px] uppercase tracking-widest ${
            data.status === 'failed' ? 'text-[#ef4444]' : 'text-[#888888]'
          }`}
        >
          Sequence {data.sequence}
        </span>
        <div
          className={`w-4 h-4 rounded-full border ${
            data.status === 'failed'
              ? 'border-[#ef4444] border-dashed'
              : data.status === 'passed'
                ? 'border-[#4f6ef7]'
                : 'border-[#2a2a2a]'
          }`}
        />
      </div>
      <h4 className="text-[16px] font-semibold text-[#f0f0f0] mb-2">{data.title}</h4>
      {data.error && (
        <p className="text-[11px] text-[#ef4444] uppercase tracking-widest mb-3">
          {data.error}
        </p>
      )}
      <div className="border-t border-[#2a2a2a] pt-3 flex items-center justify-between text-[10px] uppercase tracking-widest text-[#888888]">
        <div className="flex items-center gap-2">
          {data.icon}
          <span>{data.agent}</span>
        </div>
        <span className="font-mono text-[10px] text-[#f0f0f0]">{data.meta}</span>
      </div>
    </div>
  )
}

const ValidationLoopNode = ({ data }) => (
  <div className="w-[620px] border border-dashed border-[#2a2a2a] rounded-lg p-6 bg-[#0f0f0f]">
    <div className="flex items-center gap-2 mb-6">
      <Bug size={18} className="text-[#4f6ef7]" />
      <h3 className="text-[18px] font-semibold text-[#4f6ef7]">Validation Loop</h3>
    </div>
    <div className="grid grid-cols-2 gap-4">
      <div className="border border-[#2a2a2a] p-4 rounded bg-[#111111]">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded bg-[#2a2a2a] flex items-center justify-center">
            <Bug size={16} className="text-[#4f6ef7]" />
          </div>
          <span className="text-[10px] uppercase tracking-widest text-[#888888]">
            Debugger Agent
          </span>
        </div>
        <p className="font-mono text-[11px] text-[#4f6ef7] leading-tight">
          {data.debuggerLogs.map((line) => (
            <span key={line}>
              {line}
              <br />
            </span>
          ))}
        </p>
      </div>
      <div className="border border-[#2a2a2a] p-4 rounded bg-[#111111]">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded bg-[#2a2a2a] flex items-center justify-center">
            <Database size={16} className="text-[#4f6ef7]" />
          </div>
          <span className="text-[10px] uppercase tracking-widest text-[#888888]">
            Test Suite Execution
          </span>
        </div>
        <div className="space-y-2">
          {data.tests.map((test) => (
            <div key={test.name} className="flex justify-between items-center">
              <span className={`font-mono text-[11px] ${test.status === 'FAIL' ? 'text-[#ef4444]' : 'text-[#888888]'}`}>
                {test.name}
              </span>
              <span className={`font-mono text-[10px] ${test.status === 'FAIL' ? 'text-[#ef4444]' : 'text-[#4f6ef7]'}`}>
                {test.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
)

const nodeTypes = {
  primaryObjective: PrimaryObjectiveNode,
  divider: DividerNode,
  sequence: SequenceNode,
  validationLoop: ValidationLoopNode,
}

function WorkflowDAG({ workflow, tasks }) {
  const nodes = useMemo(() => {
    const base = [
      {
        id: 'primary',
        type: 'primaryObjective',
        position: { x: 260, y: 40 },
        data: {
          id: workflow?.id || 'workflow',
          title: workflow?.name || 'Workflow',
          description: workflow?.description || 'No description provided.',
        },
      },
      {
        id: 'divider',
        type: 'divider',
        position: { x: 390, y: 240 },
        data: {},
      },
    ]

    const taskNodes = (tasks || []).map((task, index) => {
      const agentLabel = task.current_agent || task.agent_name || 'Unassigned'
      return {
      id: task.id,
      type: 'sequence',
      position: { x: 70 + index * 310, y: 340 },
      data: {
        sequence: String(index + 1).padStart(2, '0'),
        title: task.name,
        status: task.status === 'completed' ? 'passed' : task.status === 'failed' ? 'failed' : 'pending',
        error: task.status === 'failed' ? 'FAILED' : null,
        agent: agentLabel,
        meta: task.status.toUpperCase(),
        icon:
          agentLabel === 'tester'
            ? <Shield size={16} className="text-[#888888]" />
            : agentLabel === 'debugger'
              ? <Bug size={16} className="text-[#888888]" />
              : agentLabel === 'reviewer'
                ? <Target size={16} className="text-[#888888]" />
                : agentLabel === 'planner'
                  ? <Split size={16} className="text-[#888888]" />
                  : <Database size={16} className="text-[#888888]" />,
      },
    }
    })

    return [...base, ...taskNodes]
  }, [workflow, tasks])

  const edges = useMemo(() => {
    const base = [
      {
        id: 'e1',
        source: 'primary',
        target: 'divider',
        type: 'smoothstep',
        style: { stroke: '#353535' },
      },
    ]

    const taskEdges = (tasks || []).map((task) => ({
      id: `edge-${task.id}`,
      source: 'divider',
      target: task.id,
      type: 'smoothstep',
      style: { stroke: '#353535' },
    }))

    return [...base, ...taskEdges]
  }, [tasks])

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        nodesDraggable={false}
        zoomOnScroll={false}
        panOnScroll
        className="rf-dark"
      >
        <Background gap={24} size={1} color="#2a2a2a" />
        <Controls position="bottom-right" showInteractive={false} />
      </ReactFlow>
    </div>
  )
}

export default WorkflowDAG
