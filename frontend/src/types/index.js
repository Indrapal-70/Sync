/**
 * @typedef {Object} Workflow
 * @property {string} id
 * @property {string} name
 * @property {string=} description
 * @property {'pending'|'running'|'completed'|'failed'} status
 * @property {string} created_at
 * @property {string} updated_at
 */

/**
 * @typedef {Object} Task
 * @property {string} id
 * @property {string} workflow_id
 * @property {string} name
 * @property {string=} description
 * @property {'pending'|'running'|'completed'|'failed'|'skipped'} status
 * @property {string=} agent_name
 * @property {Object<string, unknown>=} input_data
 * @property {Object<string, unknown>=} output_data
 * @property {string} created_at
 * @property {string} updated_at
 */

/**
 * @typedef {Object} WorkflowLog
 * @property {string} id
 * @property {string} workflow_id
 * @property {string=} task_id
 * @property {'info'|'warning'|'error'|'debug'} level
 * @property {string} message
 * @property {string} created_at
 */

/**
 * @typedef {Object} WebSocketMessage
 * @property {string} event
 * @property {Object<string, unknown>} payload
 * @property {string} timestamp
 */

/**
 * @typedef {Object} Agent
 * @property {string} id
 * @property {string} name
 * @property {'programmer'|'tester'|'debugger'|'researcher'|'writer'} type
 * @property {'running'|'idle'|'analyzing'|'error'} status
 * @property {string=} currentTask
 * @property {number} cpu
 * @property {string} ram
 * @property {string} nodeId
 */

export const __types = {}
