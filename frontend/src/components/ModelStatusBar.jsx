import { useEffect, useState } from 'react'
import { Cpu, Code2, AlertTriangle, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import useModelStore from '../store/modelStore'

const MODEL_CONFIG = {
  'mistral:latest': {
    displayName: 'mistral:latest',
    role: 'The Thinker',
    skills: ['plan', 'debug', 'review'],
    icon: Cpu,
    color: '#8b5cf6',
  },
  'deepseek-coder:6.7b': {
    displayName: 'deepseek-coder',
    role: 'The Builder',
    skills: ['code', 'test'],
    icon: Code2,
    color: '#4f6ef7',
  },
}

function secondsAgo(isoString) {
  if (!isoString) return null
  const diff = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000)
  if (diff < 60) return `${diff}s ago`
  return `${Math.floor(diff / 60)}m ago`
}

function ModelStatusBar() {
  const { modelHealth, allModelsOk, isLoading, lastChecked, fallbackActive, fetchModelHealth, activeSkills } =
    useModelStore()
  const [tick, setTick] = useState(0)

  // Refresh the "last checked" display every 5s
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 5000)
    return () => clearInterval(id)
  }, [])

  return (
    <div
      style={{
        background: '#111111',
        border: '1px solid #2a2a2a',
        borderRadius: 8,
        padding: '10px 12px',
        margin: '8px 8px 0 8px',
      }}
    >
      {/* Title row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 8,
        }}
      >
        <span
          style={{
            fontSize: 9,
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            color: '#888888',
            fontWeight: 600,
          }}
        >
          Model Status
        </span>
        <button
          onClick={fetchModelHealth}
          disabled={isLoading}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: '#888888',
            padding: 2,
            display: 'flex',
            alignItems: 'center',
          }}
          title="Refresh model status"
        >
          <RefreshCw
            size={11}
            style={{ animation: isLoading ? 'spin 1s linear infinite' : 'none' }}
          />
        </button>
      </div>

      {/* Model rows */}
      {Object.entries(MODEL_CONFIG).map(([modelKey, config], idx) => {
        const Icon = config.icon
        const health = modelHealth[modelKey]
        const available = health?.available
        const response_ms = health?.response_ms

        return (
          <div
            key={modelKey}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 8,
              paddingTop: 8,
              paddingBottom: 8,
              borderBottom:
                idx < Object.keys(MODEL_CONFIG).length - 1
                  ? '1px solid #2a2a2a'
                  : 'none',
            }}
          >
            {/* Icon */}
            <Icon size={14} style={{ color: config.color, flexShrink: 0, marginTop: 2 }} />

            {/* Center info */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#f0f0f0',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {config.displayName}
              </div>
              <div style={{ fontSize: 9, color: '#888888', marginBottom: 4 }}>{config.role}</div>
              {/* Skill pills */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                {config.skills.map(skill => {
                  const isActive = activeSkills?.has(skill)
                  return (
                    <span
                      key={skill}
                      style={{
                        fontSize: 9,
                        background: isActive ? `${config.color}22` : '#1a1a1a',
                        border: isActive ? `1px solid ${config.color}` : '1px solid #2a2a2a',
                        borderRadius: 3,
                        padding: '1px 5px',
                        color: isActive ? config.color : '#888888',
                        boxShadow: isActive ? `0 0 8px ${config.color}44` : 'none',
                        transition: 'all 0.3s ease',
                        animation: isActive ? 'pulse 2s ease-in-out infinite' : 'none'
                      }}
                    >
                      {skill}
                    </span>
                  )
                })}
              </div>
            </div>

            {/* Status right */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-end',
                gap: 2,
                flexShrink: 0,
              }}
            >
              {health === undefined ? (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span
                      style={{
                        width: 7,
                        height: 7,
                        borderRadius: '50%',
                        background: '#444',
                        display: 'inline-block',
                      }}
                    />
                    <span style={{ fontSize: 10, color: '#888888' }}>Checking…</span>
                  </div>
                </>
              ) : available ? (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span
                      style={{
                        width: 7,
                        height: 7,
                        borderRadius: '50%',
                        background: '#22c55e',
                        display: 'inline-block',
                        animation: 'pulse 2s ease-in-out infinite',
                      }}
                    />
                    <span style={{ fontSize: 10, color: '#22c55e' }}>Online</span>
                  </div>
                  {response_ms != null && (
                    <span style={{ fontSize: 9, color: '#888888' }}>{response_ms}ms</span>
                  )}
                </>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span
                    style={{
                      width: 7,
                      height: 7,
                      borderRadius: '50%',
                      background: '#ef4444',
                      display: 'inline-block',
                    }}
                  />
                  <span style={{ fontSize: 10, color: '#ef4444' }}>Offline</span>
                </div>
              )}
            </div>
          </div>
        )
      })}

      {/* Fallback warning */}
      {fallbackActive && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            marginTop: 8,
            padding: '5px 8px',
            background: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: 5,
          }}
        >
          <AlertTriangle size={11} style={{ color: '#f59e0b', flexShrink: 0 }} />
          <span style={{ fontSize: 9, color: '#f59e0b' }}>
            Fallback active — mistral:latest handles all skills
          </span>
        </div>
      )}

      {/* Last checked */}
      {lastChecked && (
        <div style={{ marginTop: 6, textAlign: 'right' }}>
          <span style={{ fontSize: 9, color: '#555' }}>
            Last checked: {secondsAgo(lastChecked)}
          </span>
        </div>
      )}

      {/* Pulse keyframe via a style tag injection */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

export default ModelStatusBar
