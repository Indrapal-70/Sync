const STATUS_STYLES = {
  running: {
    label: 'Running',
    className: 'bg-[#0f1a3a] text-[#4f6ef7] border-[#4f6ef7]'
  },
  analyzing: {
    label: 'Analyzing',
    className: 'bg-[#2a1f0a] text-[#f59e0b] border-[#f59e0b]'
  },
  idle: {
    label: 'Idle',
    className: 'bg-[#1a1a1a] text-[#888888] border-[#2a2a2a]'
  },
  error: {
    label: 'Error',
    className: 'bg-[#2a1010] text-[#ef4444] border-[#ef4444]'
  },
}

function StatusBadge({ status, text }) {
  const config = STATUS_STYLES[status] || STATUS_STYLES.idle
  return (
    <span
      className={`inline-flex items-center gap-2 px-2 py-1 rounded-full text-[10px] uppercase tracking-widest border ${config.className}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          status === 'running' ? 'bg-[#4f6ef7] status-pulse' : 'bg-current'
        }`}
      />
      {text || config.label}
    </span>
  )
}

export default StatusBadge
