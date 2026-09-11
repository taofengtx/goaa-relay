import type {AgentActionType,AgentAuthorizer} from './agent-action-proposals'

export type AgentActionRisk='low'|'moderate'|'high'
export type AgentExecutionMode='prepare_only'|'explicit_authorization'|'canonical_user_action'
export type AgentActionCapability={actionType:AgentActionType;risk:AgentActionRisk;authorizer:AgentAuthorizer|'either';mode:AgentExecutionMode;canExecuteFromAgentLayer:boolean;canonicalPath:string;guardrails:string[]}

export const AGENT_ACTION_CAPABILITIES:Record<AgentActionType,AgentActionCapability>={
 send_message:{actionType:'send_message',risk:'low',authorizer:'either',mode:'explicit_authorization',canExecuteFromAgentLayer:true,canonicalPath:'Order Engine messages',guardrails:['The signed-in party reviews its own outgoing message','One reviewed message per authorization','No hidden side effects','Success only after canonical API success']},
 request_information:{actionType:'request_information',risk:'moderate',authorizer:'professional',mode:'explicit_authorization',canExecuteFromAgentLayer:true,canonicalPath:'Order Engine supplement',guardrails:['Only reviewed missing items','No invented customer answers','Do not duplicate an existing supplement request']},
 start_service:{actionType:'start_service',risk:'high',authorizer:'professional',mode:'canonical_user_action',canExecuteFromAgentLayer:false,canonicalPath:'Order Engine start service',guardrails:['Verified service payment required','Accepted scope only','Keep start action in canonical professional workspace until server-side proposal audit exists']},
 prepare_delivery:{actionType:'prepare_delivery',risk:'high',authorizer:'professional',mode:'prepare_only',canExecuteFromAgentLayer:false,canonicalPath:'Order Engine delivery package',guardrails:['AI may organize draft only','Professional selects/uploads real files','No silent submission']},
 connect_professional:{actionType:'connect_professional',risk:'high',authorizer:'customer',mode:'canonical_user_action',canExecuteFromAgentLayer:false,canonicalPath:'Connect Pass / Order Engine match',guardrails:['Customer-controlled paid-access journey','No silent payment','No silent matching or reassignment']},
}
export function agentActionCapability(actionType:AgentActionType){return AGENT_ACTION_CAPABILITIES[actionType]}
export function canAgentLayerExecute(actionType:AgentActionType){return AGENT_ACTION_CAPABILITIES[actionType].canExecuteFromAgentLayer}
