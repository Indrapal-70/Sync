import { useState } from 'react'

const AGENT_PROTOTYPES = [
  { type: 'agent', agentType: 'planner',  label: 'Planner',  color: '#8b5cf6', icon: '🧠', description: 'Decomposes goals into subtasks' },
  { type: 'agent', agentType: 'coder',    label: 'Coder',    color: '#4f6ef7', icon: '💻', description: 'Writes implementation code' },
  { type: 'agent', agentType: 'tester',   label: 'Tester',   color: '#22c55e', icon: '🧪', description: 'Validates code correctness' },
  { type: 'agent', agentType: 'debugger', label: 'Debugger', color: '#f59e0b', icon: '🔧', description: 'Fixes failures and errors' },
  { type: 'agent', agentType: 'reviewer', label: 'Reviewer', color: '#06b6d4', icon: '📋', description: 'Reviews quality and scores' },
]

const SPECIAL_NODES = [
  { type: 'start', label: 'Start', color: '#22c55e', icon: '⚡', description: 'Entry point (one per canvas)' },
  { type: 'end',   label: 'End',   color: '#666666', icon: '🏁', description: 'Exit point (one per canvas)' },
]

function DraggableCard({ prototype, isSpecial }) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDragStart = (e) => {
    e.dataTransfer.setData('application/reactflow', JSON.stringify({
      agentType: prototype.agentType || prototype.type,
      label: prototype.label,
      color: prototype.color,
      icon: prototype.icon,
      nodeType: isSpecial ? prototype.type : 'agent',
    }))
    e.dataTransfer.effectAllowed = 'move'
    setIsDragging(true)
  }

  const handleDragEnd = () => {
    setIsDragging(false)
  }

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      style={{
        borderColor: isDragging ? prototype.color : `${prototype.color}66`,
        borderLeftColor: prototype.color,
        opacity: isDragging ? 0.5 : 1,
      }}
      className="agent-sidebar-card"
    >
      <div className="agent-sidebar-card-header">
        <span className="agent-sidebar-card-icon">{prototype.icon}</span>
        <span className="agent-sidebar-card-label" style={{ color: prototype.color }}>
          {prototype.label}
        </span>
      </div>
      <p className="agent-sidebar-card-desc">{prototype.description}</p>
    </div>
  )
}

function AgentSidebar() {
  return (
    <aside className="agent-sidebar">
      <div className="agent-sidebar-inner">
        <div className="agent-sidebar-section">
          <h3 className="agent-sidebar-title">AGENT NODES</h3>
          <div className="agent-sidebar-cards">
            {AGENT_PROTOTYPES.map((proto) => (
              <DraggableCard key={proto.agentType} prototype={proto} isSpecial={false} />
            ))}
          </div>
        </div>

        <div className="agent-sidebar-divider" />

        <div className="agent-sidebar-section">
          <h3 className="agent-sidebar-title">SPECIAL NODES</h3>
          <div className="agent-sidebar-cards">
            {SPECIAL_NODES.map((proto) => (
              <DraggableCard key={proto.type} prototype={proto} isSpecial={true} />
            ))}
          </div>
        </div>

        <div className="agent-sidebar-divider" />

        <div className="agent-sidebar-help">
          <p>Drag nodes onto the canvas to build your workflow graph.</p>
          <p>Connect nodes by dragging from one handle to another.</p>
        </div>
      </div>

      <style>{`
        .agent-sidebar {
          width: 200px;
          min-width: 200px;
          height: 100%;
          background: #111111;
          border-right: 1px solid #2a2a2a;
          display: flex;
          flex-direction: column;
          overflow-y: auto;
          z-index: 10;
        }
        .agent-sidebar-inner {
          padding: 12px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .agent-sidebar-section {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .agent-sidebar-title {
          font-size: 10px;
          font-weight: 600;
          letter-spacing: 0.12em;
          color: #888888;
          padding: 4px 4px 0;
          user-select: none;
        }
        .agent-sidebar-cards {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .agent-sidebar-card {
          width: 100%;
          background: #1a1a1a;
          border: 1px solid;
          border-left-width: 3px;
          border-radius: 6px;
          padding: 10px 12px;
          cursor: grab;
          transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
          user-select: none;
        }
        .agent-sidebar-card:active {
          cursor: grabbing;
        }
        .agent-sidebar-card:hover {
          background: #222222;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .agent-sidebar-card-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
        }
        .agent-sidebar-card-icon {
          font-size: 16px;
          line-height: 1;
        }
        .agent-sidebar-card-label {
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 0.03em;
        }
        .agent-sidebar-card-desc {
          font-size: 10px;
          color: #888888;
          line-height: 1.3;
          margin: 0;
        }
        .agent-sidebar-divider {
          height: 1px;
          background: #2a2a2a;
          margin: 8px 0;
        }
        .agent-sidebar-help {
          padding: 8px 4px;
        }
        .agent-sidebar-help p {
          font-size: 10px;
          color: #555555;
          line-height: 1.4;
          margin: 0 0 4px 0;
        }
      `}</style>
    </aside>
  )
}

export default AgentSidebar
