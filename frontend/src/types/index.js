/**
 * @typedef {Object} Agent
 * @property {string} id
 * @property {string} name
 * @property {'programmer'|'tester'|'debugger'|'planner'} type
 * @property {'running'|'idle'|'analyzing'|'error'} status
 * @property {string} [currentTask]
 * @property {number} cpu
 * @property {string} ram
 * @property {string} nodeId
 * @property {{cpu:number, ramPercent:number, networkMBs:number}} resources
 */

/**
 * @typedef {Object} Task
 * @property {string} id
 * @property {string} title
 * @property {string} description
 * @property {'pending'|'running'|'testing'|'completed'} status
 * @property {string} agentId
 * @property {'programmer'|'tester'|'debugger'|'planner'} agentType
 * @property {number} [progress]
 * @property {number} [coverage]
 * @property {boolean} [warning]
 * @property {string} [workflowId]
 */

/**
 * @typedef {Object} Workflow
 * @property {string} id
 * @property {string} name
 * @property {Task[]} tasks
 */

/**
 * @typedef {Object} LogEntry
 * @property {string} id
 * @property {string} agentId
 * @property {string} nodeId
 * @property {string} level
 * @property {string} message
 * @property {string} time
 */

/**
 * @typedef {Object} Alert
 * @property {string} id
 * @property {'memory'|'warning'|'success'} type
 * @property {string} level
 * @property {string} title
 * @property {string} description
 * @property {string} timeAgo
 */

export const __types = {}
