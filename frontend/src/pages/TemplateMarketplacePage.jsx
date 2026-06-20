import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { BookOpen, ExternalLink, GitFork, Globe, Lock, Plus, Search, Tag, Users, Check } from 'lucide-react'
import { templateService } from '../services/templateService'

function TemplateMarketplacePage() {
  const [marketplaceTemplates, setMarketplaceTemplates] = useState([])
  const [myTemplates, setMyTemplates] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [publishModalTemplate, setPublishModalTemplate] = useState(null)
  const [publishTags, setPublishTags] = useState('')
  const [forkSuccess, setForkSuccess] = useState(null)

  const loadData = async () => {
    setLoading(true)
    try {
      const publicTemplates = await templateService.getMarketplace()
      const allTemplates = await templateService.getAll()
      setMarketplaceTemplates(publicTemplates)
      
      // My templates are the ones that are either private or created by the user
      // Show templates that are not public so user can publish them
      const privateTemplates = allTemplates.filter(t => !t.is_public)
      setMyTemplates(privateTemplates)
    } catch (e) {
      console.error('Failed to load templates', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleFork = async (templateId) => {
    try {
      const res = await templateService.fork(templateId)
      setForkSuccess(res.name)
      await loadData()
      setTimeout(() => setForkSuccess(null), 3000)
    } catch (e) {
      alert('Failed to fork template')
    }
  }

  const handlePublish = async (e) => {
    e.preventDefault()
    if (!publishModalTemplate) return
    
    const tagsArray = publishTags
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0)
      
    try {
      await templateService.publish(publishModalTemplate.id, tagsArray)
      setPublishModalTemplate(null)
      setPublishTags('')
      await loadData()
    } catch (e) {
      alert('Failed to publish template')
    }
  }

  const handleUse = async (templateId) => {
    try {
      await templateService.use(templateId)
      await loadData()
      alert('Template usage recorded! You can now instantiate this workflow in the visual editor.')
    } catch (e) {
      console.error(e)
    }
  }

  const filteredMarketplace = marketplaceTemplates.filter(t => 
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col h-[calc(100vh-64px)] overflow-hidden bg-[#0a0a0a] text-[#f0f0f0]"
    >
      {/* Header */}
      <header className="px-6 py-4 flex flex-col md:flex-row md:items-center justify-between border-b border-[#2a2a2a] bg-[#0a0a0a]/90 backdrop-blur-sm shrink-0 gap-4">
        <div>
          <div className="flex items-center gap-2 text-[#888888] text-[10px] uppercase tracking-widest mb-1">
            <span>Marketplace</span>
            <span className="text-[#4f6ef7]">•</span>
            <span>Workflow Templates</span>
          </div>
          <h1 className="text-[20px] font-semibold text-[#f0f0f0]">Workflow Marketplace</h1>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-80">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#555]" />
            <input
              type="text"
              placeholder="Search templates & tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#111] border border-[#2a2a2a] rounded-lg pl-9 pr-4 py-2 text-[13px] text-[#f0f0f0] focus:outline-none focus:border-[#4f6ef7] transition-colors"
            />
          </div>
        </div>
      </header>

      {/* Main content scroll area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {forkSuccess && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="p-4 bg-[#22c55e]/10 border border-[#22c55e]/30 rounded-xl text-[#22c55e] flex items-center gap-3 text-[13px]"
          >
            <Check size={18} />
            <span>Successfully forked <strong>{forkSuccess}</strong> to your local templates collection!</span>
          </motion.div>
        )}

        {/* Public Templates Grid */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-[#888888]">
            <Globe size={16} />
            <h2 className="text-[14px] font-medium uppercase tracking-wider">Public Marketplace</h2>
          </div>

          {loading ? (
            <div className="text-[#888] text-[13px]">Loading marketplace templates...</div>
          ) : filteredMarketplace.length === 0 ? (
            <div className="border border-dashed border-[#2a2a2a] rounded-xl p-8 text-center text-[#555] text-[13px]">
              No public templates found matching your search.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredMarketplace.map((template) => (
                <motion.div
                  key={template.id}
                  whileHover={{ y: -2 }}
                  className="border border-[#2a2a2a] rounded-xl p-5 bg-[#111] hover:border-[#4f6ef7]/50 transition-colors flex flex-col justify-between h-[220px]"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <h3 className="font-medium text-[#f0f0f0] truncate text-[15px]">{template.name}</h3>
                      <span className="text-[10px] bg-[#2a2a2a] px-2 py-0.5 rounded text-[#888] font-mono">
                        v{template.version}
                      </span>
                    </div>

                    <p className="text-[12px] text-[#888] line-clamp-3 mb-4 leading-relaxed h-[54px]">
                      {template.description || 'No description provided.'}
                    </p>

                    <div className="flex flex-wrap gap-1 mb-4 h-[24px] overflow-hidden">
                      {template.tags?.map((tag) => (
                        <span key={tag} className="text-[9px] bg-[#4f6ef7]/10 text-[#4f6ef7] border border-[#4f6ef7]/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <Tag size={8} /> {tag}
                        </span>
                      )) || <span className="text-[#444] text-[10px]">-</span>}
                    </div>
                  </div>

                  <div className="flex items-center justify-between border-t border-[#2a2a2a]/60 pt-3 text-[11px] text-[#666]">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1">
                        <Users size={12} /> {template.author || 'Anonymous'}
                      </span>
                      <span className="font-mono">Used {template.usage_count}x</span>
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleUse(template.id)}
                        className="px-2.5 py-1 bg-[#22c55e]/10 text-[#22c55e] border border-[#22c55e]/20 rounded text-[10px] uppercase font-semibold hover:bg-[#22c55e]/20 transition-all"
                      >
                        Use
                      </button>
                      <button
                        onClick={() => handleFork(template.id)}
                        className="px-2.5 py-1 bg-[#4f6ef7] text-white rounded text-[10px] uppercase font-semibold hover:bg-[#4f6ef7]/80 transition-all flex items-center gap-1"
                      >
                        <GitFork size={10} /> Fork
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </section>

        {/* My Templates Section (To Publish) */}
        <section className="space-y-4 pt-4 border-t border-[#2a2a2a]">
          <div className="flex items-center gap-2 text-[#888888]">
            <Lock size={16} />
            <h2 className="text-[14px] font-medium uppercase tracking-wider">My Custom Templates (Local Only)</h2>
          </div>

          {loading ? (
            <div className="text-[#888] text-[13px]">Loading your templates...</div>
          ) : myTemplates.length === 0 ? (
            <div className="border border-dashed border-[#2a2a2a] rounded-xl p-8 text-center text-[#555] text-[13px]">
              You do not have any local templates to publish. Save a workflow as a template to see it here.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {myTemplates.map((template) => (
                <div
                  key={template.id}
                  className="border border-[#2a2a2a] rounded-xl p-5 bg-[#111]/40 flex flex-col justify-between h-[180px]"
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <h3 className="font-medium text-[#f0f0f0] truncate text-[14px]">{template.name}</h3>
                      <span className="text-[10px] bg-[#222] px-2 py-0.5 rounded text-[#666] font-mono">
                        v{template.version}
                      </span>
                    </div>
                    <p className="text-[12px] text-[#777] line-clamp-3 leading-relaxed">
                      {template.description || 'No description provided.'}
                    </p>
                  </div>

                  <div className="flex items-center justify-between border-t border-[#2a2a2a]/40 pt-3">
                    <span className="text-[11px] text-[#555] font-mono truncate max-w-[120px]">
                      ID: {template.id.substring(0, 8)}...
                    </span>
                    <button
                      onClick={() => setPublishModalTemplate(template)}
                      className="px-3 py-1 bg-[#4f6ef7]/10 text-[#4f6ef7] border border-[#4f6ef7]/20 rounded-lg text-[10px] uppercase font-semibold hover:bg-[#4f6ef7]/20 transition-all flex items-center gap-1"
                    >
                      <Globe size={11} /> Publish Publicly
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Publish Modal */}
      {publishModalTemplate && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-[#111] border border-[#2a2a2a] rounded-xl max-w-md w-full p-6 space-y-4"
          >
            <div>
              <h3 className="text-[16px] font-semibold text-[#f0f0f0]">Publish Template</h3>
              <p className="text-[12px] text-[#888] mt-1">
                Make <strong>{publishModalTemplate.name}</strong> visible to all users. Add custom tags to categorize it.
              </p>
            </div>

            <form onSubmit={handlePublish} className="space-y-4">
              <div>
                <label className="block text-[11px] uppercase tracking-widest text-[#888] mb-2">
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. python, backend, security"
                  value={publishTags}
                  onChange={(e) => setPublishTags(e.target.value)}
                  className="w-full bg-[#0a0a0a] border border-[#2a2a2a] rounded-lg px-4 py-2.5 text-[13px] text-[#f0f0f0] focus:outline-none focus:border-[#4f6ef7]"
                  autoFocus
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setPublishModalTemplate(null)}
                  className="px-4 py-2 border border-[#2a2a2a] rounded-lg text-[12px] text-[#888] hover:bg-[#1a1a1a]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#4f6ef7] text-white rounded-lg text-[12px] font-semibold hover:bg-[#4f6ef7]/90"
                >
                  Publish to Marketplace
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </motion.div>
  )
}

export default TemplateMarketplacePage
