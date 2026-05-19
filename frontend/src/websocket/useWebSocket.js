import { useEffect, useRef, useState, useCallback } from 'react'
import useWorkflowStore from '../store/workflowStore.js'
import useTaskStore from '../store/taskStore.js'
import useLogStore from '../store/logStore.js'
import useModelStore from '../store/modelStore.js'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

const getClientId = () => {
  const existing = localStorage.getItem('sync_client_id')
  if (existing) return existing
  const next = crypto.randomUUID()
  localStorage.setItem('sync_client_id', next)
  return next
}

const useWebSocket = () => {
  const wsRef = useRef(null)
  const reconnectTimeout = useRef()
  const [isConnected, setIsConnected] = useState(false)
  const workflowStore = useWorkflowStore()
  const taskStore = useTaskStore()
  const logStore = useLogStore()

  const routeMessage = useCallback(
    (message) => {
      const event = message.event || ''
      if (event.startsWith('workflow_')) workflowStore.handleWebSocketEvent(message)
      if (event.startsWith('task_')) taskStore.handleWebSocketEvent(message)
      if (event === 'agent_status_changed') taskStore.handleWebSocketEvent(message)
      if (event.startsWith('log_')) logStore.handleWebSocketEvent(message)
      // Model / skill events
      const modelEvents = [
        'skill_called', 'skill_completed', 'skill_failed',
        'model_fallback_used', 'skill_reassigned'
      ]
      if (modelEvents.includes(event)) {
        useModelStore.getState().handleWebSocketEvent(message)
      }
    },
    [workflowStore, taskStore, logStore],
  )

  const connect = useCallback(() => {
    const clientId = getClientId()
    const ws = new WebSocket(`${WS_URL}/ws/${clientId}`)

    ws.onopen = () => {
      setIsConnected(true)
      console.log('[WS] Connected')
      const ping = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ event: 'ping' }))
        }
      }, 30000)
      ws._pingInterval = ping
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        routeMessage(message)
      } catch (error) {
        console.error('[WS] Parse error', error)
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      if (ws._pingInterval) clearInterval(ws._pingInterval)
      console.log('[WS] Disconnected, reconnecting in 3s...')
      reconnectTimeout.current = setTimeout(connect, 3000)
    }

    ws.onerror = (err) => {
      console.error('[WS] Error', err)
    }

    wsRef.current = ws
  }, [routeMessage])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimeout.current)
      if (wsRef.current?._pingInterval) clearInterval(wsRef.current._pingInterval)
      wsRef.current?.close()
    }
  }, [connect])

  const sendMessage = (msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }

  return { isConnected, sendMessage }
}

export default useWebSocket
