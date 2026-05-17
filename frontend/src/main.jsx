import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import useWebSocket from './websocket/useWebSocket.js'

function WebSocketBootstrap() {
  useWebSocket()
  return null
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <WebSocketBootstrap />
      <App />
    </BrowserRouter>
  </StrictMode>,
)
