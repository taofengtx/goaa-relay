import type {AgentActionType} from './agent-action-proposals'

/**
 * Golden Flow is a frozen business baseline.
 * This module is intentionally declarative: it does not alter canonical routes.
 * Any change to Golden business semantics requires explicit owner approval.
 */
export const GOLDEN_FLOW_STEPS=[
 'consultation',
 'planning',
 '30_day_personal_ai_agent_access_39_90',
 'connect_and_match',
 'professional_estimate',
 'customer_acceptance',
 'professional_service_payment',
 'service_execution',
 'supplement',
 'delivery',
 'customer_confirmed_completion',
] as const

export const GOLDEN_FLOW_INVARIANTS=[
 'Agent Layer augments Golden Flow; it never replaces it.',
 'No Agent Layer action may create a second payment, matching, estimate, delivery, or completion state machine.',
 'Matching is not completion.',
 'Payment is not completion.',
 'Starting service is not completion.',
 'Delivery is not completion.',
 'Only canonical customer-confirmed completed state closes the Matter.',
 'A generic continue instruction is not approval to modify Golden Flow.',
] as const

const AGENT_LAYER_SAFE_ACTIONS=new Set<AgentActionType>(['send_message','request_information'])
export function isPostGoldenAgentAction(actionType:AgentActionType){return AGENT_LAYER_SAFE_ACTIONS.has(actionType)}
export function assertPostGoldenAgentAction(actionType:AgentActionType){if(!isPostGoldenAgentAction(actionType))throw new Error(`GOLDEN_FLOW_BOUNDARY: ${actionType} must remain in its canonical workflow unless separately approved.`)}
