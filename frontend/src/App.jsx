import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout.jsx'
import OrchestrationPage from './pages/OrchestrationPage.jsx'
import WorkflowsPage from './pages/WorkflowsPage.jsx'
import AgentFleetPage from './pages/AgentFleetPage.jsx'
import KanbanPage from './pages/KanbanPage.jsx'
import NodeBuilderPage from './pages/NodeBuilderPage.jsx'
import TerminalLogsPage from './pages/TerminalLogsPage.jsx'
import ProjectSettingsPage from './pages/ProjectSettingsPage.jsx'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/orchestration" replace />} />
      <Route element={<AppLayout />}>
        <Route path="/orchestration" element={<OrchestrationPage />} />
        <Route path="/workflows" element={<KanbanPage />} />
        <Route path="/workflows/:id" element={<WorkflowsPage />} />
        <Route path="/workflows/:id/builder" element={<NodeBuilderPage />} />
        <Route path="/agents" element={<AgentFleetPage />} />
        <Route path="/agents/:id" element={<AgentFleetPage />} />
        <Route path="/logs" element={<TerminalLogsPage />} />
        <Route path="/settings" element={<ProjectSettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/orchestration" replace />} />
    </Routes>
  )
}

export default App
