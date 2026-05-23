import { useState, useEffect, useCallback } from 'react'
import { X, Check } from 'lucide-react'

/* ─────────────────────────────────────────────────────
   AGENT CONFIG (matches NodeBuilderPage)
   ───────────────────────────────────────────────────── */
const AGENT_OPTIONS = [
  { value: 'planner',  label: 'Planner',  color: '#8b5cf6', icon: '🧠' },
  { value: 'coder',    label: 'Coder',    color: '#4f6ef7', icon: '💻' },
  { value: 'tester',   label: 'Tester',   color: '#22c55e', icon: '🧪' },
  { value: 'debugger', label: 'Debugger', color: '#f59e0b', icon: '🔧' },
  { value: 'reviewer', label: 'Reviewer', color: '#06b6d4', icon: '📋' },
]

/* ─────────────────────────────────────────────────────
   MINI PREVIEW NODE
   ───────────────────────────────────────────────────── */
function MiniPreviewNode({ data }) {
  const displayLabel = data.taskName || data.label || 'Untitled'
  const agentCfg = AGENT_OPTIONS.find((a) => a.value === data.agentType)
  const color = agentCfg?.color || data.color || '#888'
  const icon = agentCfg?.icon || data.icon || '🤖'

  return (
    <div className="ncp-preview-node" style={{ borderColor: color }}>
      <div className="ncp-preview-accent" style={{ background: color }} />
      <div className="ncp-preview-body">
        <div className="ncp-preview-header">
          <span className="ncp-preview-icon">{icon}</span>
          <span className="ncp-preview-label">{displayLabel}</span>
        </div>
        <span
          className="ncp-preview-badge"
          style={{ background: `${color}22`, color, borderColor: `${color}44` }}
        >
          {data.agentType}
        </span>
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────────────
   NODE CONFIG PANEL
   ───────────────────────────────────────────────────── */
function NodeConfigPanel({ node, onUpdate, onClose }) {
  const [taskName, setTaskName] = useState('')
  const [taskDescription, setTaskDescription] = useState('')
  const [agentType, setAgentType] = useState('coder')
  const [expectedOutput, setExpectedOutput] = useState('')
  const [maxRetries, setMaxRetries] = useState('')
  const [applied, setApplied] = useState(false)

  // Validation errors
  const [errors, setErrors] = useState({})
  const [touched, setTouched] = useState({})

  // Sync from node prop when it changes
  useEffect(() => {
    if (node) {
      setTaskName(node.data.taskName || '')
      setTaskDescription(node.data.taskDescription || '')
      setAgentType(node.data.agentType || 'coder')
      setExpectedOutput(node.data.expectedOutput || '')
      setMaxRetries(node.data.maxRetries !== undefined && node.data.maxRetries !== '' ? String(node.data.maxRetries) : '')
      setErrors({})
      setTouched({})
      setApplied(false)
    }
  }, [node?.id])

  // Validate on change
  useEffect(() => {
    const newErrors = {}
    if (touched.taskName && (!taskName || taskName.trim() === '')) {
      newErrors.taskName = 'Task name is required'
    } else if (taskName.length > 80) {
      newErrors.taskName = 'Max 80 characters'
    }
    if (touched.taskDescription && (!taskDescription || taskDescription.trim().length < 10)) {
      newErrors.taskDescription = 'Minimum 10 characters'
    } else if (taskDescription.length > 1000) {
      newErrors.taskDescription = 'Max 1000 characters'
    }
    if (maxRetries !== '' && (isNaN(Number(maxRetries)) || Number(maxRetries) < 0 || Number(maxRetries) > 5)) {
      newErrors.maxRetries = 'Must be 0-5'
    }
    setErrors(newErrors)
  }, [taskName, taskDescription, maxRetries, touched])

  const hasErrors = Object.keys(errors).length > 0
  const isValid = taskName.trim() !== '' && taskDescription.trim().length >= 10 && !hasErrors

  const handleBlur = (field) => {
    setTouched((prev) => ({ ...prev, [field]: true }))
  }

  const handleApply = useCallback(() => {
    // Force-touch all fields
    setTouched({ taskName: true, taskDescription: true, maxRetries: true })

    if (!taskName.trim() || taskDescription.trim().length < 10) return

    onUpdate(node.id, {
      taskName: taskName.trim(),
      taskDescription: taskDescription.trim(),
      agentType,
      expectedOutput: expectedOutput.trim(),
      maxRetries: maxRetries !== '' ? Number(maxRetries) : '',
    })

    setApplied(true)
    setTimeout(() => setApplied(false), 1500)
  }, [node, taskName, taskDescription, agentType, expectedOutput, maxRetries, onUpdate])

  if (!node) return null

  const agentCfg = AGENT_OPTIONS.find((a) => a.value === agentType)
  const panelColor = agentCfg?.color || '#888'

  // Preview data
  const previewData = {
    taskName,
    label: agentCfg?.label || agentType,
    agentType,
    color: panelColor,
    icon: agentCfg?.icon || '🤖',
  }

  return (
    <div className="ncp-overlay">
      {/* Color bar */}
      <div className="ncp-colorbar" style={{ background: panelColor }} />

      {/* Header */}
      <div className="ncp-header">
        <div className="ncp-header-left">
          <span className="ncp-header-icon">{agentCfg?.icon || '🤖'}</span>
          <span className="ncp-header-title" style={{ color: panelColor }}>
            {agentCfg?.label?.toUpperCase() || 'AGENT'} NODE
          </span>
        </div>
        <button className="ncp-close" onClick={onClose}>
          <X size={16} />
        </button>
      </div>

      {/* Form */}
      <div className="ncp-form">
        {/* Task Name */}
        <div className="ncp-field">
          <div className="ncp-field-label-row">
            <label className="ncp-label">Task Name</label>
            <span className="ncp-counter">{taskName.length}/80</span>
          </div>
          <input
            type="text"
            value={taskName}
            onChange={(e) => setTaskName(e.target.value)}
            onBlur={() => handleBlur('taskName')}
            placeholder="e.g. Implement the core algorithm"
            className={`ncp-input ${errors.taskName ? 'ncp-input-error' : ''}`}
            maxLength={80}
          />
          {errors.taskName && <p className="ncp-error">{errors.taskName}</p>}
          <p className="ncp-hint">A short label shown on the canvas node</p>
        </div>

        {/* Task Prompt */}
        <div className="ncp-field">
          <div className="ncp-field-label-row">
            <label className="ncp-label">Task Prompt</label>
            <span className="ncp-counter">{taskDescription.length}/1000</span>
          </div>
          <textarea
            value={taskDescription}
            onChange={(e) => setTaskDescription(e.target.value)}
            onBlur={() => handleBlur('taskDescription')}
            placeholder="Describe exactly what this agent should do. Be specific — this becomes the agent's prompt."
            className={`ncp-input ncp-textarea ${errors.taskDescription ? 'ncp-input-error' : ''}`}
            rows={5}
          />
          {errors.taskDescription && <p className="ncp-error">{errors.taskDescription}</p>}
          <p className="ncp-hint">This is sent directly to the agent as its instruction.</p>
        </div>

        {/* Agent Type */}
        <div className="ncp-field">
          <label className="ncp-label">Agent Type</label>
          <div className="ncp-select-wrapper">
            <select
              value={agentType}
              onChange={(e) => setAgentType(e.target.value)}
              className="ncp-select"
            >
              {AGENT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.icon} {opt.label}
                </option>
              ))}
            </select>
            <div className="ncp-select-dot" style={{ background: panelColor }} />
          </div>
        </div>

        {/* Expected Output */}
        <div className="ncp-field">
          <label className="ncp-label">Expected Output <span className="ncp-optional">(optional)</span></label>
          <input
            type="text"
            value={expectedOutput}
            onChange={(e) => setExpectedOutput(e.target.value)}
            placeholder="e.g. A Python function with tests"
            className="ncp-input"
          />
          <p className="ncp-hint">Helps the reviewer agent evaluate correctness</p>
        </div>

        {/* Max Retries */}
        <div className="ncp-field">
          <label className="ncp-label">Max Retries <span className="ncp-optional">(optional)</span></label>
          <input
            type="number"
            value={maxRetries}
            onChange={(e) => setMaxRetries(e.target.value)}
            onBlur={() => handleBlur('maxRetries')}
            placeholder="Leave blank for default"
            min={0}
            max={5}
            className={`ncp-input ${errors.maxRetries ? 'ncp-input-error' : ''}`}
          />
          {errors.maxRetries && <p className="ncp-error">{errors.maxRetries}</p>}
          <p className="ncp-hint">Leave blank to use the global skill setting</p>
        </div>

        {/* Live Preview */}
        <div className="ncp-preview-section">
          <label className="ncp-label">LIVE PREVIEW</label>
          <div className="ncp-preview-container">
            <MiniPreviewNode data={previewData} />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="ncp-footer">
        <button
          className={`ncp-apply-btn ${applied ? 'ncp-apply-success' : ''}`}
          onClick={handleApply}
          disabled={!isValid && Object.keys(touched).length > 0}
        >
          {applied ? (
            <>
              <Check size={14} /> Applied
            </>
          ) : (
            'Apply Changes'
          )}
        </button>
      </div>

      <style>{`
        .ncp-overlay {
          position: absolute;
          right: 0;
          top: 0;
          bottom: 0;
          width: 300px;
          background: #1a1a1a;
          border-left: 1px solid #2a2a2a;
          display: flex;
          flex-direction: column;
          z-index: 30;
          box-shadow: -8px 0 24px rgba(0,0,0,0.3);
          animation: ncp-slide-in 0.2s ease-out;
        }
        @keyframes ncp-slide-in {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        .ncp-colorbar {
          height: 4px;
          width: 100%;
          flex-shrink: 0;
        }
        .ncp-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          border-bottom: 1px solid #2a2a2a;
          background: #151515;
        }
        .ncp-header-left {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .ncp-header-icon {
          font-size: 18px;
        }
        .ncp-header-title {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.1em;
        }
        .ncp-close {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
          border-radius: 6px;
          border: none;
          background: transparent;
          color: #888888;
          cursor: pointer;
          transition: color 0.15s, background 0.15s;
        }
        .ncp-close:hover {
          color: #f0f0f0;
          background: rgba(255,255,255,0.05);
        }
        .ncp-form {
          flex: 1;
          overflow-y: auto;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .ncp-field {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .ncp-field-label-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .ncp-label {
          font-size: 10px;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #888888;
        }
        .ncp-optional {
          font-weight: 400;
          text-transform: lowercase;
          letter-spacing: 0;
          color: #555555;
        }
        .ncp-counter {
          font-size: 9px;
          color: #555555;
          font-variant-numeric: tabular-nums;
        }
        .ncp-input {
          width: 100%;
          background: #111111;
          border: 1px solid #2a2a2a;
          border-radius: 6px;
          color: #f0f0f0;
          font-size: 12px;
          padding: 8px 10px;
          transition: border-color 0.15s;
          font-family: inherit;
        }
        .ncp-input:focus {
          outline: none;
          border-color: #4f6ef7;
        }
        .ncp-input::placeholder {
          color: #444444;
        }
        .ncp-input-error {
          border-color: #ef4444 !important;
        }
        .ncp-textarea {
          resize: vertical;
          min-height: 80px;
          line-height: 1.5;
        }
        .ncp-error {
          font-size: 10px;
          color: #ef4444;
          margin: 0;
        }
        .ncp-hint {
          font-size: 10px;
          color: #555555;
          margin: 0;
          line-height: 1.3;
        }
        .ncp-select-wrapper {
          position: relative;
        }
        .ncp-select {
          width: 100%;
          appearance: none;
          background: #111111;
          border: 1px solid #2a2a2a;
          border-radius: 6px;
          color: #f0f0f0;
          font-size: 12px;
          padding: 8px 10px 8px 24px;
          cursor: pointer;
          font-family: inherit;
        }
        .ncp-select:focus {
          outline: none;
          border-color: #4f6ef7;
        }
        .ncp-select-dot {
          position: absolute;
          left: 10px;
          top: 50%;
          transform: translateY(-50%);
          width: 8px;
          height: 8px;
          border-radius: 50%;
          pointer-events: none;
        }

        /* ── Preview ── */
        .ncp-preview-section {
          padding-top: 8px;
          border-top: 1px solid #2a2a2a;
        }
        .ncp-preview-container {
          display: flex;
          justify-content: center;
          padding: 12px;
          background: #0a0a0a;
          border-radius: 8px;
          border: 1px solid #2a2a2a;
          margin-top: 8px;
        }
        .ncp-preview-node {
          background: #1a1a1a;
          border: 1.5px solid;
          border-radius: 8px;
          min-width: 140px;
          position: relative;
        }
        .ncp-preview-accent {
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 4px;
          border-radius: 8px 0 0 8px;
        }
        .ncp-preview-body {
          padding: 8px 10px 8px 14px;
        }
        .ncp-preview-header {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 4px;
        }
        .ncp-preview-icon {
          font-size: 14px;
        }
        .ncp-preview-label {
          font-size: 11px;
          font-weight: 600;
          color: #f0f0f0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .ncp-preview-badge {
          display: inline-block;
          font-size: 8px;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          padding: 1px 6px;
          border-radius: 3px;
          border: 1px solid;
        }

        /* ── Footer ── */
        .ncp-footer {
          padding: 12px 16px;
          border-top: 1px solid #2a2a2a;
          background: #151515;
        }
        .ncp-apply-btn {
          width: 100%;
          padding: 10px;
          border: none;
          border-radius: 6px;
          background: #4f6ef7;
          color: #fff;
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 0.03em;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          transition: background 0.15s, opacity 0.15s;
        }
        .ncp-apply-btn:hover {
          background: #3d5bd6;
        }
        .ncp-apply-btn:disabled {
          opacity: 0.4;
          cursor: not-allowed;
        }
        .ncp-apply-success {
          background: #22c55e !important;
        }
      `}</style>
    </div>
  )
}

export default NodeConfigPanel
