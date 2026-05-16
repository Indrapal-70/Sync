import { motion } from 'framer-motion'

function TerminalLogsPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="p-8 text-[#888888]"
    >
      Terminal Logs placeholder.
    </motion.div>
  )
}

export default TerminalLogsPage
