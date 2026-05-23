import { motion } from 'framer-motion'
import { FileQuestion, Home } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="flex flex-col items-center justify-center h-[calc(100vh-64px)] p-8 text-center"
    >
      <div className="bg-[#111111] border border-[#2a2a2a] rounded-2xl p-12 max-w-md w-full shadow-2xl flex flex-col items-center">
        <div className="w-20 h-20 bg-[#1a1a1a] rounded-full flex items-center justify-center mb-6 border border-[#2a2a2a]">
          <FileQuestion size={36} className="text-[#4f6ef7]" />
        </div>
        <h1 className="text-[24px] font-semibold text-[#f0f0f0] mb-2">Page Not Found</h1>
        <p className="text-[14px] text-[#888888] mb-8 leading-relaxed">
          The page you are looking for doesn't exist or has been moved. Check the URL or return home.
        </p>
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 bg-[#4f6ef7] text-white px-6 py-3 rounded-xl font-medium hover:bg-[#3d59c9] transition-colors shadow-[0_0_24px_rgba(79,110,247,0.25)] hover:shadow-[0_0_32px_rgba(79,110,247,0.4)]"
        >
          <Home size={18} />
          Return to Dashboard
        </button>
      </div>
    </motion.div>
  )
}

export default NotFoundPage
