import {agentActionCapability} from './agent-action-capabilities'
import {isPostGoldenAgentAction} from './golden-flow-boundary'
import type {AgentActionProposal} from './agent-action-proposals'

export type ProposalIntegrity={pass:boolean;checks:{label:string;pass:boolean}[]}
export function checkProposalIntegrity(proposal:AgentActionProposal):ProposalIntegrity{
 const capability=agentActionCapability(proposal.actionType)
 const authorizerAllowed=capability.authorizer==='either'||capability.authorizer===proposal.authorizer
 const payloadBound=JSON.stringify(proposal.payloadPreview||{}).length<=8192
 const arraysBound=proposal.willHappen.length<=20&&proposal.willNotHappen.length<=20
 const executableBoundary=!capability.canExecuteFromAgentLayer||isPostGoldenAgentAction(proposal.actionType)
 const retrySane=!proposal.retryOf||proposal.retryOf!==proposal.id
 const checks=[
  {label:'Authorizer matches the action capability',pass:authorizerAllowed},
  {label:'Payload preview stays within the frontend safety bound',pass:payloadBound},
  {label:'Action disclosure arrays stay bounded',pass:arraysBound},
  {label:'Executable capability stays inside the Post-Golden boundary',pass:executableBoundary},
  {label:'Retry does not self-reference',pass:retrySane},
 ]
 return{pass:checks.every(x=>x.pass),checks}
}
