import { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  getBezierPath,
  BaseEdge,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Trash2, Play, Save, RotateCcw, X } from 'lucide-react'
import AgentSidebar from '../components/AgentSidebar'
import NodeConfigPanel from '../components/NodeConfigPanel'

/* ─────────────────────────────────────────────────────
   AGENT CONFIG (shared reference for colors/icons)
   ───────────────────────────────────────────────────── */
const AGENT_CONFIG = {
  planner:  { color: '#8b5cf6', icon: '🧠', label: 'Planner' },
  coder:    { color: '#4f6ef7', icon: '💻', label: 'Coder' },
  tester:   { color: '#22c55e', icon: '🧪', label: 'Tester' },
  debugger: { color: '#f59e0b', icon: '🔧', label: 'Debugger' },
  reviewer: { color: '#06b6d4', icon: '📋', label: 'Reviewer' },
}

/* ─────────────────────────────────────────────────────
   CUSTOM NODE: AgentNode
   ───────────────────────────────────────────────────── */
function AgentNode({ id, data, selected }) {
  const { setNodes, setEdges } = useReactFlow()

  const deleteNode = useCallback((e) => {
    e.stopPropagation()
    setNodes((nds) => nds.filter((n) => n.id !== id))
    setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id))
  }, [id, setNodes, setEdges])

  const displayLabel = data.taskName || data.label
  const isPlaceholder = !data.taskName

  return (
    <div
      className="agent-node"
      style={{
        borderColor: selected ? '#ffffff' : data.color,
        boxShadow: selected ? `0 0 16px ${data.color}44` : 'none',
      }}
    >
      <div className="agent-node-accent" style={{ background: data.color }} />

      <Handle type="target" position={Position.Top} className="agent-node-handle" />

      <div className="agent-node-body">
        <div className="agent-node-header">
          <span className="agent-node-icon">{data.icon}</span>
          <span
            className={`agent-node-label ${isPlaceholder ? 'agent-node-label-placeholder' : ''}`}
          >
            {displayLabel}
          </span>
          <button
            className="agent-node-delete"
            onClick={deleteNode}
            title="Delete node"
          >
            <X size={12} />
          </button>
        </div>
        <span
          className="agent-node-badge"
          style={{ background: `${data.color}22`, color: data.color, borderColor: `${data.color}44` }}
        >
          {data.agentType}
        </span>
      </div>

      <Handle type="source" position={Position.Bottom} className="agent-node-handle" />
    </div>
  )
}

/* ─────────────────────────────────────────────────────
   CUSTOM NODE: StartNode
   ───────────────────────────────────────────────────── */
function StartNode({ selected }) {
  return (
    <div
      className="start-node"
      style={{
        borderColor: selected ? '#ffffff' : '#22c55e',
        boxShadow: selected ? '0 0 16px rgba(34,197,94,0.3)' : 'none',
      }}
    >
      <span className="start-node-icon">⚡</span>
      <span className="start-node-label">START</span>
      <Handle type="source" position={Position.Bottom} className="agent-node-handle" />
    </div>
  )
}

/* ─────────────────────────────────────────────────────
   CUSTOM NODE: EndNode
   ───────────────────────────────────────────────────── */
function EndNode({ selected }) {
  return (
    <div
      className="end-node"
      style={{
        borderColor: selected ? '#ffffff' : '#444444',
        boxShadow: selected ? '0 0 16px rgba(68,68,68,0.3)' : 'none',
      }}
    >
      <span className="end-node-icon">🏁</span>
      <span className="end-node-label">END</span>
      <Handle type="target" position={Position.Top} className="agent-node-handle" />
    </div>
  )
}

/* ─────────────────────────────────────────────────────
   CUSTOM EDGE: ButtonEdge (with hover delete)
   ───────────────────────────────────────────────────── */
function ButtonEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, style = {} }) {
  const { setEdges } = useReactFlow()
  const [hovered, setHovered] = useState(false)

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX, sourceY, sourcePosition,
    targetX, targetY, targetPosition,
  })

  const deleteEdge = (e) => {
    e.stopPropagation()
    setEdges((eds) => eds.filter((edge) => edge.id !== id))
  }

  return (
    <>
      {/* Invisible wider path for easier hover detection */}
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={20}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      />
      <BaseEdge
        path={edgePath}
        style={{
          stroke: '#4f6ef7',
          strokeWidth: 2,
          ...style,
        }}
        markerEnd="url(#arrow-marker)"
      />
      {hovered && (
        <foreignObject
          width={24}
          height={24}
          x={labelX - 12}
          y={labelY - 12}
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
        >
          <button
            className="edge-delete-btn"
            onClick={deleteEdge}
            title="Delete edge"
          >
            <X size={12} />
          </button>
        </foreignObject>
      )}
    </>
  )
}

/* ─────────────────────────────────────────────────────
   CYCLE DETECTION (topological sort)
   ───────────────────────────────────────────────────── */
function hasCycle(nodes, edges) {
  const nodeIds = new Set(nodes.map((n) => n.id))
  const adj = new Map()
  const inDegree = new Map()
  nodeIds.forEach((id) => { adj.set(id, []); inDegree.set(id, 0) })
  edges.forEach((e) => {
    if (nodeIds.has(e.source) && nodeIds.has(e.target)) {
      adj.get(e.source).push(e.target)
      inDegree.set(e.target, (inDegree.get(e.target) || 0) + 1)
    }
  })
  const queue = []
  inDegree.forEach((deg, id) => { if (deg === 0) queue.push(id) })
  let visited = 0
  while (queue.length > 0) {
    const curr = queue.shift()
    visited++
    for (const neighbor of adj.get(curr) || []) {
      inDegree.set(neighbor, inDegree.get(neighbor) - 1)
      if (inDegree.get(neighbor) === 0) queue.push(neighbor)
    }
  }
  return visited !== nodeIds.size
}

/* ─────────────────────────────────────────────────────
   GRAPH VALIDATION
   ───────────────────────────────────────────────────── */
function validateGraph(nodes, edges) {
  const errors = []
  const agentNodes = nodes.filter((n) => n.type === 'agentNode')
  const startNode = nodes.find((n) => n.type === 'startNode')
  const endNode = nodes.find((n) => n.type === 'endNode')

  // 1. Must have at least one agent node
  if (agentNodes.length === 0) {
    errors.push('Must have at least one agent node')
  }

  // 2. START must have at least one outgoing edge
  if (startNode) {
    const startEdges = edges.filter((e) => e.source === startNode.id)
    if (startEdges.length === 0) {
      errors.push('START node must have at least one outgoing edge')
    }
  }

  // 3. END must have at least one incoming edge
  if (endNode) {
    const endEdges = edges.filter((e) => e.target === endNode.id)
    if (endEdges.length === 0) {
      errors.push('END node must have at least one incoming edge')
    }
  }

  // 4. No orphan agent nodes
  agentNodes.forEach((node) => {
    const hasEdge = edges.some((e) => e.source === node.id || e.target === node.id)
    if (!hasEdge) {
      errors.push(`Node "${node.data.taskName || node.data.label}" is disconnected`)
    }
  })

  // 5. No cycles
  if (hasCycle(nodes, edges)) {
    errors.push('Graph contains a cycle — remove circular dependencies')
  }

  // 6. Every agent node must have a non-empty taskName
  agentNodes.forEach((node) => {
    if (!node.data.taskName || node.data.taskName.trim() === '') {
      errors.push(`Node "${node.data.label}" is missing a task name`)
    }
  })

  return errors
}

/* ─────────────────────────────────────────────────────
   INITIAL NODES
   ───────────────────────────────────────────────────── */
const INITIAL_NODES = [
  {
    id: 'start-node',
    type: 'startNode',
    position: { x: 100, y: 200 },
    data: { label: 'START' },
    deletable: false,
  },
  {
    id: 'end-node',
    type: 'endNode',
    position: { x: 700, y: 200 },
    data: { label: 'END' },
    deletable: false,
  },
]

/* ─────────────────────────────────────────────────────
   MAIN COMPONENT (inner, needs ReactFlowProvider)
   ───────────────────────────────────────────────────── */
function NodeBuilderInner() {
  const reactFlowWrapper = useRef(null)
  const reactFlowInstance = useReactFlow()

  const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES)
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [configPanelOpen, setConfigPanelOpen] = useState(false)
  const [graphName, setGraphName] = useState('')
  const [contextMenu, setContextMenu] = useState(null)
  const [undoStack, setUndoStack] = useState([])
  const [saveModal, setSaveModal] = useState(false)
  const [templateName, setTemplateName] = useState('')
  const [templateDesc, setTemplateDesc] = useState('')

  // ─── Custom node/edge types ──────────────────────
  const nodeTypes = useMemo(() => ({
    agentNode: AgentNode,
    startNode: StartNode,
    endNode: EndNode,
  }), [])

  const edgeTypes = useMemo(() => ({
    default: ButtonEdge,
  }), [])

  // ─── Validation ──────────────────────────────────
  const validationErrors = useMemo(
    () => validateGraph(nodes, edges),
    [nodes, edges]
  )

  // ─── Undo stack push helper ──────────────────────
  const pushUndo = useCallback(() => {
    setUndoStack((prev) => {
      const snap = { nodes: JSON.parse(JSON.stringify(nodes)), edges: JSON.parse(JSON.stringify(edges)) }
      const next = [snap, ...prev]
      return next.slice(0, 20)
    })
  }, [nodes, edges])

  // ─── Drop handler ────────────────────────────────
  const onDrop = useCallback((event) => {
    event.preventDefault()
    const rawData = event.dataTransfer.getData('application/reactflow')
    if (!rawData) return

    const nodeData = JSON.parse(rawData)

    // Prevent multiple START or END nodes
    if (nodeData.nodeType === 'start') {
      const hasStart = nodes.some((n) => n.type === 'startNode')
      if (hasStart) return
    }
    if (nodeData.nodeType === 'end') {
      const hasEnd = nodes.some((n) => n.type === 'endNode')
      if (hasEnd) return
    }

    const bounds = reactFlowWrapper.current.getBoundingClientRect()
    const position = reactFlowInstance.project({
      x: event.clientX - bounds.left,
      y: event.clientY - bounds.top,
    })

    pushUndo()

    if (nodeData.nodeType === 'start') {
      const newNode = {
        id: `start-node-${Date.now()}`,
        type: 'startNode',
        position,
        data: { label: 'START' },
        deletable: false,
      }
      setNodes((prev) => [...prev, newNode])
      return
    }
    if (nodeData.nodeType === 'end') {
      const newNode = {
        id: `end-node-${Date.now()}`,
        type: 'endNode',
        position,
        data: { label: 'END' },
        deletable: false,
      }
      setNodes((prev) => [...prev, newNode])
      return
    }

    const newNode = {
      id: `node-${Date.now()}`,
      type: 'agentNode',
      position,
      data: {
        agentType: nodeData.agentType,
        label: nodeData.label,
        taskName: '',
        taskDescription: '',
        expectedOutput: '',
        maxRetries: '',
        color: nodeData.color,
        icon: nodeData.icon,
      },
    }
    setNodes((prev) => [...prev, newNode])
  }, [nodes, reactFlowInstance, pushUndo, setNodes])

  const onDragOver = useCallback((event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  // ─── Connect handler ─────────────────────────────
  const onConnect = useCallback((params) => {
    if (params.source === params.target) return
    const exists = edges.some(
      (e) => e.source === params.source && e.target === params.target
    )
    if (exists) return

    pushUndo()
    setEdges((prev) =>
      addEdge(
        {
          ...params,
          type: 'default',
          animated: false,
          style: { stroke: '#4f6ef7', strokeWidth: 2 },
          markerEnd: { type: 'arrowclosed', color: '#4f6ef7' },
        },
        prev
      )
    )
  }, [edges, pushUndo, setEdges])

  // ─── Connection validation ───────────────────────
  const isValidConnection = useCallback((connection) => {
    if (connection.source === connection.target) return false
    const sourceNode = nodes.find((n) => n.id === connection.source)
    if (sourceNode?.type === 'endNode') return false
    const targetNode = nodes.find((n) => n.id === connection.target)
    if (targetNode?.type === 'startNode') return false
    return true
  }, [nodes])

  // ─── Node click → open config panel ──────────────
  const onNodeClick = useCallback((event, node) => {
    if (node.type === 'startNode' || node.type === 'endNode') return
    setSelectedNode(node)
    setConfigPanelOpen(true)
  }, [])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
    setConfigPanelOpen(false)
    setContextMenu(null)
  }, [])

  // ─── Node update from config panel ───────────────
  const onNodeUpdate = useCallback((nodeId, newData) => {
    // If agent type changed, update color/icon
    const agentCfg = AGENT_CONFIG[newData.agentType]
    const extra = agentCfg ? { color: agentCfg.color, icon: agentCfg.icon, label: agentCfg.label } : {}

    setNodes((prev) =>
      prev.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...newData, ...extra } }
          : node
      )
    )
    // Also update selectedNode reference so panel stays in sync
    setSelectedNode((prev) => {
      if (prev && prev.id === nodeId) {
        return { ...prev, data: { ...prev.data, ...newData, ...extra } }
      }
      return prev
    })
  }, [setNodes])

  // ─── Keyboard shortcuts ──────────────────────────
  useEffect(() => {
    const handler = (e) => {
      // Ignore if focus is in an input/textarea
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return

      // Ctrl+Z: undo
      if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
        e.preventDefault()
        setUndoStack((prev) => {
          if (prev.length === 0) return prev
          const [last, ...rest] = prev
          setNodes(last.nodes)
          setEdges(last.edges)
          return rest
        })
        return
      }

      // Ctrl+A: select all nodes
      if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
        e.preventDefault()
        setNodes((nds) => nds.map((n) => ({ ...n, selected: true })))
        return
      }

      // Escape: deselect, close panel
      if (e.key === 'Escape') {
        setSelectedNode(null)
        setConfigPanelOpen(false)
        setContextMenu(null)
        setNodes((nds) => nds.map((n) => ({ ...n, selected: false })))
        setEdges((eds) => eds.map((e) => ({ ...e, selected: false })))
        return
      }

      // Delete / Backspace: delete selected (except start/end)
      if (e.key === 'Delete' || e.key === 'Backspace') {
        pushUndo()
        const selectedNodeIds = nodes
          .filter((n) => n.selected && n.type !== 'startNode' && n.type !== 'endNode')
          .map((n) => n.id)
        if (selectedNodeIds.length > 0) {
          setNodes((nds) => nds.filter((n) => !selectedNodeIds.includes(n.id)))
          setEdges((eds) =>
            eds.filter((e) => !selectedNodeIds.includes(e.source) && !selectedNodeIds.includes(e.target))
          )
        }
        // Also delete selected edges
        setEdges((eds) => eds.filter((e) => !e.selected))
        return
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [nodes, edges, pushUndo, setNodes, setEdges])

  // ─── Context menu (right-click) ──────────────────
  const onPaneContextMenu = useCallback((event) => {
    event.preventDefault()
    const bounds = reactFlowWrapper.current.getBoundingClientRect()
    setContextMenu({
      x: event.clientX - bounds.left,
      y: event.clientY - bounds.top,
      flowX: event.clientX,
      flowY: event.clientY,
    })
  }, [])

  const addNodeFromContext = useCallback((agentType) => {
    if (!contextMenu) return
    const bounds = reactFlowWrapper.current.getBoundingClientRect()
    const position = reactFlowInstance.project({
      x: contextMenu.flowX - bounds.left,
      y: contextMenu.flowY - bounds.top,
    })
    const cfg = AGENT_CONFIG[agentType]
    pushUndo()
    const newNode = {
      id: `node-${Date.now()}`,
      type: 'agentNode',
      position,
      data: {
        agentType,
        label: cfg.label,
        taskName: '',
        taskDescription: '',
        expectedOutput: '',
        maxRetries: '',
        color: cfg.color,
        icon: cfg.icon,
      },
    }
    setNodes((prev) => [...prev, newNode])
    setContextMenu(null)
  }, [contextMenu, reactFlowInstance, pushUndo, setNodes])

  // ─── Clear canvas ────────────────────────────────
  const clearCanvas = useCallback(() => {
    if (!window.confirm('Clear all nodes and edges? START and END will remain.')) return
    pushUndo()
    setNodes(INITIAL_NODES)
    setEdges([])
    setSelectedNode(null)
    setConfigPanelOpen(false)
  }, [pushUndo, setNodes, setEdges])

  // ─── Delete selected (multi-select) ──────────────
  const deleteSelected = useCallback(() => {
    pushUndo()
    const selectedIds = nodes
      .filter((n) => n.selected && n.type !== 'startNode' && n.type !== 'endNode')
      .map((n) => n.id)
    setNodes((nds) => nds.filter((n) => !selectedIds.includes(n.id)))
    setEdges((eds) => {
      const filtered = eds.filter(
        (e) => !selectedIds.includes(e.source) && !selectedIds.includes(e.target)
      )
      return filtered.filter((e) => !e.selected)
    })
  }, [nodes, pushUndo, setNodes, setEdges])

  // ─── Save as template stub ───────────────────────
  const handleSaveTemplate = useCallback(() => {
    setSaveModal(true)
    setTemplateName(graphName || '')
    setTemplateDesc('')
  }, [graphName])

  const confirmSaveTemplate = useCallback(() => {
    // Placeholder — will be wired to POST /api/templates in Batch 2
    console.log('[NodeBuilder] Save as template:', {
      name: templateName,
      description: templateDesc,
      nodes,
      edges,
    })
    setSaveModal(false)
    alert('Template save will be connected in the next batch.')
  }, [templateName, templateDesc, nodes, edges])

  const handleExecuteNow = useCallback(() => {
    if (validationErrors.length > 0) {
      alert(`Cannot execute: ${validationErrors[0]}`)
      return
    }
    // Placeholder — will be wired in Batch 2
    console.log('[NodeBuilder] Execute now:', { nodes, edges })
    alert('Execute will be connected in the next batch.')
  }, [validationErrors, nodes, edges])

  // ─── Selected count for toolbar ──────────────────
  const selectedCount = nodes.filter(
    (n) => n.selected && n.type !== 'startNode' && n.type !== 'endNode'
  ).length

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="nb-container"
    >
      {/* ── TOP TOOLBAR ────────────────────────────── */}
      <div className="nb-toolbar">
        <div className="nb-toolbar-left">
          <span className="nb-toolbar-title">Visual Workflow Editor</span>
          <span className="nb-toolbar-badge">Beta</span>
        </div>
        <div className="nb-toolbar-center">
          <input
            type="text"
            value={graphName}
            onChange={(e) => setGraphName(e.target.value)}
            placeholder="Untitled Graph"
            className="nb-toolbar-name-input"
          />
        </div>
        <div className="nb-toolbar-right">
          {selectedCount > 0 && (
            <button className="nb-toolbar-btn nb-toolbar-btn-danger" onClick={deleteSelected}>
              <Trash2 size={14} /> Delete ({selectedCount})
            </button>
          )}
          <button className="nb-toolbar-btn" onClick={clearCanvas}>
            <RotateCcw size={14} /> Clear
          </button>
          <button className="nb-toolbar-btn" onClick={handleSaveTemplate}>
            <Save size={14} /> Save Template
          </button>
          <button className="nb-toolbar-btn nb-toolbar-btn-primary" onClick={handleExecuteNow}>
            <Play size={14} /> Execute Now
          </button>
        </div>
      </div>

      {/* ── MAIN AREA ──────────────────────────────── */}
      <div className="nb-main">
        <AgentSidebar />

        <div className="nb-canvas-area" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onPaneContextMenu={onPaneContextMenu}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            isValidConnection={isValidConnection}
            defaultEdgeOptions={{ type: 'default' }}
            fitView
            deleteKeyCode={null}
            multiSelectionKeyCode="Shift"
            className="rf-dark"
          >
            <Background color="#2a2a2a" gap={16} />
            <Controls showInteractive={false} />
            <MiniMap
              nodeColor={(n) => n.data?.color || '#888'}
              maskColor="rgba(0,0,0,0.7)"
              style={{ background: '#111111', border: '1px solid #2a2a2a' }}
            />
            {/* SVG marker for arrow edges */}
            <svg style={{ position: 'absolute', width: 0, height: 0 }}>
              <defs>
                <marker
                  id="arrow-marker"
                  viewBox="0 0 10 10"
                  refX="8"
                  refY="5"
                  markerWidth={8}
                  markerHeight={8}
                  orient="auto-start-reverse"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#4f6ef7" />
                </marker>
              </defs>
            </svg>
          </ReactFlow>

          {/* Context menu */}
          <AnimatePresence>
            {contextMenu && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.1 }}
                className="nb-context-menu"
                style={{ left: contextMenu.x, top: contextMenu.y }}
              >
                {Object.entries(AGENT_CONFIG).map(([type, cfg]) => (
                  <button
                    key={type}
                    className="nb-context-item"
                    onClick={() => addNodeFromContext(type)}
                  >
                    <span style={{ color: cfg.color }}>{cfg.icon}</span>
                    <span>Add {cfg.label} Node</span>
                  </button>
                ))}
                <div className="nb-context-divider" />
                <button
                  className="nb-context-item"
                  onClick={() => { reactFlowInstance.fitView(); setContextMenu(null) }}
                >
                  <span>📐</span>
                  <span>Fit View</span>
                </button>
                <button
                  className="nb-context-item"
                  onClick={() => { clearCanvas(); setContextMenu(null) }}
                >
                  <span>🗑️</span>
                  <span>Clear Canvas</span>
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Shortcut hints */}
          <div className="nb-shortcut-hints">
            Del: delete · Ctrl+Z: undo · Esc: deselect · Right-click: menu
          </div>

          {/* NodeConfigPanel (right drawer) */}
          {configPanelOpen && selectedNode && (
            <NodeConfigPanel
              node={selectedNode}
              onUpdate={onNodeUpdate}
              onClose={() => { setConfigPanelOpen(false); setSelectedNode(null) }}
            />
          )}
        </div>
      </div>

      {/* ── VALIDATION BAR ─────────────────────────── */}
      <div className={`nb-validation-bar ${validationErrors.length > 0 ? 'nb-validation-error' : 'nb-validation-ok'}`}>
        {validationErrors.length === 0 ? (
          <span>✓ Graph is valid</span>
        ) : (
          <span>
            ⚠ {validationErrors.length} error{validationErrors.length > 1 ? 's' : ''}: {validationErrors[0]}
          </span>
        )}
      </div>

      {/* ── SAVE MODAL ─────────────────────────────── */}
      <AnimatePresence>
        {saveModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="nb-modal-overlay"
            onClick={() => setSaveModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="nb-modal"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="nb-modal-title">Save as Template</h3>
              <div className="nb-modal-field">
                <label>Template Name</label>
                <input
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  placeholder="My Workflow Template"
                  className="nb-modal-input"
                />
              </div>
              <div className="nb-modal-field">
                <label>Description</label>
                <textarea
                  value={templateDesc}
                  onChange={(e) => setTemplateDesc(e.target.value)}
                  placeholder="Describe what this workflow does..."
                  rows={3}
                  className="nb-modal-input"
                />
              </div>
              <div className="nb-modal-actions">
                <button className="nb-toolbar-btn" onClick={() => setSaveModal(false)}>Cancel</button>
                <button
                  className="nb-toolbar-btn nb-toolbar-btn-primary"
                  onClick={confirmSaveTemplate}
                  disabled={!templateName.trim()}
                >
                  Save Template
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── STYLES ─────────────────────────────────── */}
      <style>{`
        .nb-container {
          height: calc(100vh - 64px);
          display: flex;
          flex-direction: column;
          background: #0a0a0a;
          overflow: hidden;
        }

        /* ── Toolbar ── */
        .nb-toolbar {
          height: 48px;
          min-height: 48px;
          background: #0a0a0a;
          border-bottom: 1px solid #2a2a2a;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 16px;
          z-index: 20;
        }
        .nb-toolbar-left {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .nb-toolbar-title {
          font-size: 14px;
          font-weight: 600;
          color: #f0f0f0;
        }
        .nb-toolbar-badge {
          font-size: 9px;
          font-weight: 700;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          background: linear-gradient(135deg, #4f6ef7, #8b5cf6);
          color: #fff;
          padding: 2px 8px;
          border-radius: 10px;
        }
        .nb-toolbar-center {
          flex: 1;
          display: flex;
          justify-content: center;
        }
        .nb-toolbar-name-input {
          background: transparent;
          border: 1px solid transparent;
          border-radius: 6px;
          color: #f0f0f0;
          font-size: 13px;
          text-align: center;
          padding: 4px 16px;
          width: 240px;
          transition: border-color 0.15s, background 0.15s;
        }
        .nb-toolbar-name-input:hover {
          border-color: #2a2a2a;
        }
        .nb-toolbar-name-input:focus {
          outline: none;
          border-color: #4f6ef7;
          background: #111111;
        }
        .nb-toolbar-name-input::placeholder {
          color: #555555;
        }
        .nb-toolbar-right {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .nb-toolbar-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 11px;
          font-weight: 500;
          letter-spacing: 0.03em;
          padding: 6px 12px;
          border-radius: 6px;
          border: 1px solid #2a2a2a;
          background: #1a1a1a;
          color: #f0f0f0;
          cursor: pointer;
          transition: background 0.15s, border-color 0.15s;
          white-space: nowrap;
        }
        .nb-toolbar-btn:hover {
          background: #2a2a2a;
          border-color: #3a3a3a;
        }
        .nb-toolbar-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        .nb-toolbar-btn-primary {
          background: #4f6ef7;
          border-color: #4f6ef7;
          color: #fff;
        }
        .nb-toolbar-btn-primary:hover {
          background: #3d5bd6;
        }
        .nb-toolbar-btn-danger {
          border-color: #ef4444;
          color: #ef4444;
        }
        .nb-toolbar-btn-danger:hover {
          background: #2a1010;
        }

        /* ── Main area ── */
        .nb-main {
          flex: 1;
          display: flex;
          min-height: 0;
          position: relative;
        }
        .nb-canvas-area {
          flex: 1;
          position: relative;
          min-height: 0;
        }

        /* ── Validation bar ── */
        .nb-validation-bar {
          height: 32px;
          min-height: 32px;
          display: flex;
          align-items: center;
          padding: 0 16px;
          font-size: 11px;
          font-weight: 500;
          letter-spacing: 0.03em;
          border-top: 1px solid #2a2a2a;
        }
        .nb-validation-ok {
          color: #22c55e;
          background: #0a0a0a;
        }
        .nb-validation-error {
          color: #ef4444;
          background: #0f0808;
        }

        /* ── Agent node ── */
        .agent-node {
          background: #1a1a1a;
          border: 1.5px solid;
          border-radius: 8px;
          min-width: 160px;
          position: relative;
          transition: border-color 0.15s, box-shadow 0.2s;
        }
        .agent-node-accent {
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 4px;
          border-radius: 8px 0 0 8px;
        }
        .agent-node-body {
          padding: 10px 12px 10px 16px;
        }
        .agent-node-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 6px;
        }
        .agent-node-icon {
          font-size: 18px;
          line-height: 1;
        }
        .agent-node-label {
          flex: 1;
          font-size: 12px;
          font-weight: 600;
          color: #f0f0f0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .agent-node-label-placeholder {
          font-style: italic;
          color: #555555;
        }
        .agent-node-delete {
          width: 18px;
          height: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: none;
          background: transparent;
          color: #555555;
          cursor: pointer;
          border-radius: 4px;
          transition: color 0.15s, background 0.15s;
          padding: 0;
        }
        .agent-node-delete:hover {
          color: #ef4444;
          background: rgba(239,68,68,0.15);
        }
        .agent-node-badge {
          display: inline-block;
          font-size: 9px;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          padding: 2px 8px;
          border-radius: 4px;
          border: 1px solid;
        }
        .agent-node-handle {
          width: 8px !important;
          height: 8px !important;
          background: #f0f0f0 !important;
          border: 2px solid #0a0a0a !important;
        }

        /* ── Start node ── */
        .start-node {
          background: #0f2a1a;
          border: 2px solid #22c55e;
          border-radius: 10px;
          padding: 10px 20px;
          display: flex;
          align-items: center;
          gap: 8px;
          min-width: 100px;
          justify-content: center;
          transition: border-color 0.15s, box-shadow 0.2s;
        }
        .start-node-icon {
          font-size: 16px;
        }
        .start-node-label {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.1em;
          color: #22c55e;
        }

        /* ── End node ── */
        .end-node {
          background: #1a1a1a;
          border: 2px solid #444444;
          border-radius: 10px;
          padding: 10px 20px;
          display: flex;
          align-items: center;
          gap: 8px;
          min-width: 100px;
          justify-content: center;
          transition: border-color 0.15s, box-shadow 0.2s;
        }
        .end-node-icon {
          font-size: 16px;
        }
        .end-node-label {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.1em;
          color: #888888;
        }

        /* ── Edge delete button ── */
        .edge-delete-btn {
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          border: 1px solid #ef4444;
          background: #2a1010;
          color: #ef4444;
          cursor: pointer;
          transition: background 0.15s;
        }
        .edge-delete-btn:hover {
          background: #3a1515;
        }

        /* ── Context menu ── */
        .nb-context-menu {
          position: absolute;
          z-index: 50;
          background: #1a1a1a;
          border: 1px solid #2a2a2a;
          border-radius: 8px;
          padding: 4px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.5);
          min-width: 180px;
        }
        .nb-context-item {
          display: flex;
          align-items: center;
          gap: 8px;
          width: 100%;
          padding: 8px 12px;
          font-size: 12px;
          color: #f0f0f0;
          background: transparent;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          text-align: left;
          transition: background 0.1s;
        }
        .nb-context-item:hover {
          background: #2a2a2a;
        }
        .nb-context-divider {
          height: 1px;
          background: #2a2a2a;
          margin: 4px 0;
        }

        /* ── Shortcut hints ── */
        .nb-shortcut-hints {
          position: absolute;
          bottom: 8px;
          right: 8px;
          font-size: 10px;
          color: #444444;
          z-index: 5;
          pointer-events: none;
          user-select: none;
        }

        /* ── Save modal ── */
        .nb-modal-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.6);
          backdrop-filter: blur(4px);
          z-index: 100;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .nb-modal {
          background: #1a1a1a;
          border: 1px solid #2a2a2a;
          border-radius: 12px;
          padding: 24px;
          width: 400px;
          max-width: 90vw;
          box-shadow: 0 16px 48px rgba(0,0,0,0.5);
        }
        .nb-modal-title {
          font-size: 16px;
          font-weight: 600;
          color: #f0f0f0;
          margin: 0 0 16px;
        }
        .nb-modal-field {
          margin-bottom: 12px;
        }
        .nb-modal-field label {
          display: block;
          font-size: 11px;
          font-weight: 500;
          letter-spacing: 0.05em;
          text-transform: uppercase;
          color: #888888;
          margin-bottom: 4px;
        }
        .nb-modal-input {
          width: 100%;
          background: #111111;
          border: 1px solid #2a2a2a;
          border-radius: 6px;
          color: #f0f0f0;
          font-size: 13px;
          padding: 8px 12px;
          transition: border-color 0.15s;
          resize: vertical;
        }
        .nb-modal-input:focus {
          outline: none;
          border-color: #4f6ef7;
        }
        .nb-modal-actions {
          display: flex;
          justify-content: flex-end;
          gap: 8px;
          margin-top: 16px;
        }

        /* ── React Flow overrides ── */
        .react-flow__minimap {
          border-radius: 8px !important;
          overflow: hidden;
        }
        .react-flow__controls {
          border-radius: 8px !important;
          border: 1px solid #2a2a2a !important;
          box-shadow: none !important;
        }
        .react-flow__controls-button {
          background: #1a1a1a !important;
          border-bottom: 1px solid #2a2a2a !important;
          color: #f0f0f0 !important;
        }
        .react-flow__controls-button:hover {
          background: #2a2a2a !important;
        }
        .react-flow__controls-button svg {
          fill: #f0f0f0 !important;
        }
      `}</style>
    </motion.div>
  )
}

/* ─────────────────────────────────────────────────────
   WRAPPER — provides ReactFlowProvider
   ───────────────────────────────────────────────────── */
function NodeBuilderPage() {
  return (
    <ReactFlowProvider>
      <NodeBuilderInner />
    </ReactFlowProvider>
  )
}

export default NodeBuilderPage
