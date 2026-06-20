import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { analyticsService } from '../services/analyticsService'
import { Activity, ShieldAlert, Award, Clock } from 'lucide-react'

export default function AnalyticsDashboardPage() {
  const [days, setDays] = useState(7)
  const [performance, setPerformance] = useState([])
  const [healing, setHealing] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      setLoading(true)
      try {
        const perfData = await analyticsService.getAgentPerformance(days)
        const healData = await analyticsService.getHealingSummary(days)
        setPerformance(perfData)
        setHealing(healData)
      } catch (err) {
        console.error('Failed to load analytics', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [days])

  const successRateData = performance.map(agent => ({
    name: agent.agent_name.replace('Agent', ''),
    rate: Math.round(agent.success_rate * 100),
    runs: agent.total_runs,
    passed: agent.passed,
    failed: agent.failed
  }))

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#f0f0f0] p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex justify-between items-center border-b border-[#2a2a2a] pb-6">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-[#4f6ef7] to-[#8b5cf6] bg-clip-text text-transparent">
              Platform Analytics
            </h1>
            <p className="text-sm text-[#888888] mt-1">
              Real-time multi-agent performance and system healing statistics
            </p>
          </div>
          <div className="flex gap-2">
            {[1, 7, 30].map(d => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-4 py-2 text-xs font-semibold rounded-lg border transition-all cursor-pointer ${
                  days === d
                    ? 'bg-[#4f6ef7] text-[#0a0a0a] border-[#4f6ef7]'
                    : 'bg-[#1a1a1a] text-[#888888] border-[#2a2a2a] hover:border-[#4f6ef7]/40'
                }`}
              >
                {d === 1 ? 'Last 24 Hours' : `Last ${d} Days`}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-96">
            <span className="text-sm text-[#888888] animate-pulse">Loading analytics...</span>
          </div>
        ) : (
          <>
            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              
              <motion.div 
                whileHover={{ y: -4 }}
                className="bg-[#1a1a1a]/60 backdrop-blur-md border border-[#2a2a2a] rounded-xl p-6 flex items-center gap-4 hover:border-[#4f6ef7]/40 transition-colors"
              >
                <div className="p-3 bg-[#4f6ef7]/10 rounded-lg text-[#4f6ef7]">
                  <Activity size={24} />
                </div>
                <div>
                  <span className="text-xs text-[#888888] uppercase tracking-wider block font-medium">Total Healing Runs</span>
                  <span className="text-2xl font-bold font-mono text-[#f0f0f0]">{healing?.total_healing_cycles || 0}</span>
                </div>
              </motion.div>

              <motion.div 
                whileHover={{ y: -4 }}
                className="bg-[#1a1a1a]/60 backdrop-blur-md border border-[#2a2a2a] rounded-xl p-6 flex items-center gap-4 hover:border-[#22c55e]/40 transition-colors"
              >
                <div className="p-3 bg-[#22c55e]/10 rounded-lg text-[#22c55e]">
                  <Award size={24} />
                </div>
                <div>
                  <span className="text-xs text-[#888888] uppercase tracking-wider block font-medium">Resolved Loops</span>
                  <span className="text-2xl font-bold font-mono text-[#f0f0f0]">{healing?.resolved || 0}</span>
                </div>
              </motion.div>

              <motion.div 
                whileHover={{ y: -4 }}
                className="bg-[#1a1a1a]/60 backdrop-blur-md border border-[#2a2a2a] rounded-xl p-6 flex items-center gap-4 hover:border-[#ef4444]/40 transition-colors"
              >
                <div className="p-3 bg-[#ef4444]/10 rounded-lg text-[#ef4444]">
                  <ShieldAlert size={24} />
                </div>
                <div>
                  <span className="text-xs text-[#888888] uppercase tracking-wider block font-medium">Unresolved Loops</span>
                  <span className="text-2xl font-bold font-mono text-[#f0f0f0]">{healing?.unresolved || 0}</span>
                </div>
              </motion.div>

              <motion.div 
                whileHover={{ y: -4 }}
                className="bg-[#1a1a1a]/60 backdrop-blur-md border border-[#2a2a2a] rounded-xl p-6 flex items-center gap-4 hover:border-[#8b5cf6]/40 transition-colors"
              >
                <div className="p-3 bg-[#8b5cf6]/10 rounded-lg text-[#8b5cf6]">
                  <Clock size={24} />
                </div>
                <div>
                  <span className="text-xs text-[#888888] uppercase tracking-wider block font-medium">Avg Cycles / Task</span>
                  <span className="text-2xl font-bold font-mono text-[#f0f0f0]">{healing?.avg_cycles_per_task?.toFixed(1) || '0.0'}</span>
                </div>
              </motion.div>

            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              
              {/* Chart 1: Success Rates */}
              <div className="bg-[#111111] border border-[#2a2a2a] rounded-xl p-6">
                <h3 className="text-lg font-semibold mb-6 text-[#f0f0f0] flex items-center gap-2">
                  <span>📊</span> Agent Success Rates (%)
                </h3>
                <div className="h-80 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={successRateData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                      <XAxis dataKey="name" stroke="#888" fontSize={12} />
                      <YAxis stroke="#888" fontSize={12} domain={[0, 100]} />
                      <Tooltip 
                        contentStyle={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
                        labelStyle={{ color: '#fff', fontWeight: 600 }}
                      />
                      <Bar dataKey="rate" fill="#4f6ef7" radius={[4, 4, 0, 0]}>
                        {successRateData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.rate > 80 ? '#22c55e' : entry.rate > 50 ? '#f59e0b' : '#ef4444'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Chart 2: Healing Insights / Breakdown */}
              <div className="bg-[#111111] border border-[#2a2a2a] rounded-xl p-6 flex flex-col justify-between">
                <div>
                  <h3 className="text-lg font-semibold mb-6 text-[#f0f0f0] flex items-center gap-2">
                    <span>🔧</span> Healing Breakdown & Failures
                  </h3>
                  
                  {healing?.total_healing_cycles > 0 ? (
                    <div className="space-y-6">
                      <div className="flex justify-between items-center border-b border-[#2a2a2a] pb-4">
                        <span className="text-[#888888] text-sm">Most Common Failed Agent</span>
                        <span className="font-mono bg-[#ef4444]/10 text-[#ef4444] border border-[#ef4444]/20 px-3 py-1 rounded text-xs font-semibold uppercase">
                          {healing.most_common_failed_agent || 'None'}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center border-b border-[#2a2a2a] pb-4">
                        <span className="text-[#888888] text-sm">Auto-Healing Resolution Rate</span>
                        <span className="font-mono text-[#22c55e] text-lg font-bold">
                          {((healing.resolved / healing.total_healing_cycles) * 100).toFixed(0)}%
                        </span>
                      </div>
                      
                      <div>
                        <span className="text-[#888888] text-sm block mb-2">Healing Process Funnel</span>
                        <div className="w-full h-3 bg-[#2a2a2a] rounded-full overflow-hidden flex">
                          <div 
                            className="bg-[#22c55e]" 
                            style={{ width: `${(healing.resolved / healing.total_healing_cycles) * 100}%` }}
                            title={`Resolved: ${healing.resolved}`}
                          />
                          <div 
                            className="bg-[#ef4444]" 
                            style={{ width: `${(healing.unresolved / healing.total_healing_cycles) * 100}%` }}
                            title={`Unresolved: ${healing.unresolved}`}
                          />
                        </div>
                        <div className="flex justify-between text-[11px] text-[#555555] mt-1.5 font-mono">
                          <span>Resolved ({healing.resolved})</span>
                          <span>Unresolved ({healing.unresolved})</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col justify-center items-center h-48 text-[#555555]">
                      <span className="text-4xl">🕊️</span>
                      <span className="text-sm mt-3">No healing cycles recorded in this timeframe</span>
                    </div>
                  )}
                </div>
              </div>

            </div>
          </>
        )}
      </div>
    </div>
  )
}
