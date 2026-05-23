export function graphToTemplate(nodes, edges, templateName, description = '') {
  // 1. Filter out START and END nodes
  const agentNodes = nodes.filter(n =>
    n.type !== 'startNode' && n.type !== 'endNode')

  // 2. Build a dependency map from edges
  //    Edge source -> target means target depends on source
  const dependencyMap = {}
  agentNodes.forEach(n => { dependencyMap[n.id] = [] })
  edges.forEach(edge => {
    const source = nodes.find(n => n.id === edge.source)
    const target = nodes.find(n => n.id === edge.target)
    // Skip edges involving START or END nodes
    if (!source || !target) return
    if (source.type === 'startNode' || target.type === 'endNode') return
    if (dependencyMap[edge.target]) {
      dependencyMap[edge.target].push(edge.source)
    }
  })

  // 3. Build task_blueprints array
  const task_blueprints = agentNodes.map(node => ({
    node_id:      node.id,
    name:         node.data.taskName || node.data.label,
    description:  node.data.taskDescription || '',
    agent_hint:   node.data.agentType,
    expected_output: node.data.expectedOutput || '',
    max_retries_override: node.data.maxRetriesOverride || null,
    dependencies: dependencyMap[node.id] || [],
  }))

  // 4. Infer model hints
  const builderAgents = ['coder', 'tester']
  const builderCount = agentNodes.filter(n =>
    builderAgents.includes(n.data.agentType)).length
  const thinkerCount = agentNodes.length - builderCount
  const model_hints = {
    builder_heavy: builderCount > thinkerCount,
    thinker_heavy: thinkerCount >= builderCount,
  }

  return {
    name: templateName,
    description,
    category: 'custom',
    tasks_schema: task_blueprints, // Note: mapping task_blueprints to tasks_schema for backend compat
    model_hints,
    source: 'visual_editor',
  }
}

export function validateGraph(nodes, edges) {
  const errors = []
  const agentNodes = nodes.filter(n =>
    n.type !== 'startNode' && n.type !== 'endNode')

  if (agentNodes.length === 0)
    errors.push('Add at least one agent node to the canvas.')

  const startNode = nodes.find(n => n.type === 'startNode')
  const endNode   = nodes.find(n => n.type === 'endNode')
  if (startNode && !edges.some(e => e.source === startNode.id))
    errors.push('START node must have at least one outgoing connection.')
  if (endNode && !edges.some(e => e.target === endNode.id))
    errors.push('END node must have at least one incoming connection.')

  agentNodes.forEach(node => {
    const hasEdge = edges.some(e => e.source === node.id || e.target === node.id)
    if (!hasEdge)
      errors.push(`Node "${node.data.label}" is disconnected — connect it or remove it.`)
    if (!node.data.taskName?.trim())
      errors.push(`Node "${node.data.label}" needs a Task Name — click it to edit.`)
  })

  // Cycle detection via DFS
  const adj = {}
  nodes.forEach(n => { adj[n.id] = [] })
  edges.forEach(e => {
    if (adj[e.source]) adj[e.source].push(e.target)
  })
  
  const visited = {}; const inStack = {}
  let hasCycle = false
  const dfs = (nodeId) => {
    visited[nodeId] = true; inStack[nodeId] = true
    for (const neighbor of (adj[nodeId] || [])) {
      if (!visited[neighbor]) dfs(neighbor)
      else if (inStack[neighbor]) hasCycle = true
    }
    inStack[nodeId] = false
  }
  
  nodes.forEach(n => { if (!visited[n.id]) dfs(n.id) })
  if (hasCycle)
    errors.push('Cycle detected — your graph has a loop. Remove the circular connection.')

  return errors
}
