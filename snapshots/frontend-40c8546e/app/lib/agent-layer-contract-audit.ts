import {AGENT_ACTION_CAPABILITIES} from './agent-action-capabilities'
import {GOLDEN_FLOW_INVARIANTS,isPostGoldenAgentAction} from './golden-flow-boundary'
import type {AgentActionType} from './agent-action-proposals'

export type AgentLayerContractAudit={pass:boolean;checks:{label:string;pass:boolean}[]}

export function auditAgentLayerContract():AgentLayerContractAudit{
 const types=Object.keys(AGENT_ACTION_CAPABILITIES) as AgentActionType[]
 const executable=types.filter(t=>AGENT_ACTION_CAPABILITIES[t].canExecuteFromAgentLayer)
 const expectedSafe=['send_message','request_information'] as AgentActionType[]
 const exactExecutable=executable.length===expectedSafe.length&&expectedSafe.every(t=>executable.includes(t))
 const safeMatches=types.every(t=>isPostGoldenAgentAction(t)===AGENT_ACTION_CAPABILITIES[t].canExecuteFromAgentLayer)
 const highRiskLocked=(['start_service','prepare_delivery','connect_professional'] as AgentActionType[]).every(t=>!AGENT_ACTION_CAPABILITIES[t].canExecuteFromAgentLayer)
 const completionLocked=GOLDEN_FLOW_INVARIANTS.some(x=>x.includes('Only canonical customer-confirmed completed state closes the Matter.'))
 const noSecondStateMachine=GOLDEN_FLOW_INVARIANTS.some(x=>x.includes('No Agent Layer action may create a second payment, matching, estimate, delivery, or completion state machine.'))
 const checks=[
  {label:'Only message and information-request actions are Agent-executable',pass:exactExecutable},
  {label:'Golden-safe action set matches executable capability set',pass:safeMatches},
  {label:'Start service, delivery, and professional connection remain locked to canonical workflows',pass:highRiskLocked},
  {label:'Customer-confirmed completion invariant is present',pass:completionLocked},
  {label:'Second Golden state machines are explicitly prohibited',pass:noSecondStateMachine},
 ]
 return{pass:checks.every(x=>x.pass),checks}
}
