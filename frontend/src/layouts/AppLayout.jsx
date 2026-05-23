import { useEffect } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  Activity,
  Bell,
  BookOpen,
  Bot,
  GitBranch,
  LayoutDashboard,
  ScrollText,
  Settings,
  SlidersHorizontal,
  Network
} from 'lucide-react'
import ModelStatusBar from '../components/ModelStatusBar'
import useModelStore from '../store/modelStore'

const navItems = [
  { label: 'Orchestration', icon: LayoutDashboard, to: '/orchestration' },
  { label: 'Workflows', icon: GitBranch, to: '/workflows' },
  { label: 'Visual Editor', icon: Network, to: '/builder' },
  { label: 'Agent Fleet', icon: Bot, to: '/agents' },
  { label: 'Terminal Logs', icon: ScrollText, to: '/logs' },
  { label: 'Project Settings', icon: Settings, to: '/settings' },
]

const footerItems = [
  { label: 'Documentation', icon: BookOpen, to: '/docs' },
  { label: 'System Status', icon: Activity, to: '/status' },
]

function AppLayout() {
  const location = useLocation()
  const fetchAll = useModelStore(state => state.fetchAll)
  const fetchModelHealth = useModelStore(state => state.fetchModelHealth)

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchModelHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-[#f0f0f0] flex">
      <aside className="hidden md:flex flex-col h-screen sticky left-0 top-0 py-6 bg-[#111111] border-r border-[#2a2a2a] w-[280px] shrink-0">
        <div className="px-6 mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-[#1a1a1a] border border-[#2a2a2a] flex items-center justify-center overflow-hidden">
              <img src="/logo.png" alt="SYNC Logo" className="w-full h-full object-cover" />
            </div>
            <div>
              <h2 className="text-[18px] font-semibold">Sync</h2>
              <p className="text-[10px] uppercase tracking-widest text-[#888888] mt-1">
                Active Session: 42m
              </p>
            </div>
          </div>
          <button className="w-full mt-4 py-2 px-4 rounded border border-[#2a2a2a] bg-[#1a1a1a] text-[10px] uppercase tracking-widest text-[#f0f0f0] hover:bg-[#2a2a2a] transition-colors">
            Deploy New Agent
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto px-2 space-y-1 text-[12px] uppercase tracking-widest">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname.startsWith(item.to)
            return (
              <NavLink
                key={item.label}
                to={item.to}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors duration-150 ${
                  isActive
                    ? 'bg-[#1a1a1a] text-[#4f6ef7] border-r-4 border-[#4f6ef7]'
                    : 'text-[#888888] hover:text-[#f0f0f0] hover:bg-[#1a1a1a]'
                }`}
              >
                <Icon size={18} className={isActive ? 'text-[#4f6ef7]' : ''} />
                <span>{item.label}</span>
              </NavLink>
            )
          })}
        </nav>
        <ModelStatusBar />
        <div className="mt-auto px-4 pb-4 border-t border-[#2a2a2a] pt-4">
          <div className="space-y-1 text-[12px] uppercase tracking-widest">
            {footerItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.label}
                  to={item.to}
                  className="flex items-center gap-3 px-4 py-2 rounded text-[#888888] hover:text-[#f0f0f0] hover:bg-[#1a1a1a] transition-colors"
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </div>
        </div>
      </aside>

      <div className="flex-1 min-w-0 flex flex-col">
        <header className="h-16 px-4 md:px-6 border-b border-[#2a2a2a] bg-[#0a0a0a]/80 backdrop-blur-xl sticky top-0 z-40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#1a1a1a] border border-[#2a2a2a] flex items-center justify-center overflow-hidden md:hidden">
              <img src="/logo.png" alt="SYNC Logo" className="w-full h-full object-cover" />
            </div>
            <span className="font-semibold text-[18px] md:hidden">Sync</span>
          </div>
          <div className="flex items-center gap-3">
            <button className="p-2 rounded-full text-[#888888] hover:text-[#f0f0f0] hover:bg-white/5 transition-colors">
              <Bell size={18} />
            </button>
            <button className="p-2 rounded-full text-[#888888] hover:text-[#f0f0f0] hover:bg-white/5 transition-colors">
              <SlidersHorizontal size={18} />
            </button>
            <button className="p-2 rounded-full text-[#888888] hover:text-[#f0f0f0] hover:bg-white/5 transition-colors">
              <Settings size={18} />
            </button>
            <div className="w-8 h-8 rounded-full border border-[#2a2a2a] bg-[#1a1a1a]" />
          </div>
        </header>

        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AppLayout
