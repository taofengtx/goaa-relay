import {agentActionCapability} from './agent-action-capabilities'
import {isPostGoldenAgentAction} from './golden-flow-boundary'
import type {AgentActionProposal} from './agent-action-proposals'

export type AgentActionReadiness={ready:boolean;checks:{label:string;pass:boolean}[];reason:string}

export function evaluateAgentActionReadiness(proposal:AgentActionProposal,token?:string|null):AgentActionReadiness{
 const capability=agentActionCapability(proposal.actionType)
 const payload=proposal.payloadPreview||{}
 const payloadReady=proposal.actionType==='send_message'
  ? typeof payload.message==='string'&&payload.message.trim().length>0
  : proposal.actionType==='request_information'
   ? Array.isArray(payload.items)&&payload.items.length>0
   : false
 const checks=[
  {label:'Explicit human approval recorded',pass:proposal.status==='approved'||proposal.status==='executing'},
  {label:'Signed-in canonical role token available',pass:Boolean(token)},
  {label:'Action is allowed above the frozen Golden Flow',pass:isPostGoldenAgentAction(proposal.actionType)},
  {label:'Capability explicitly allows Agent-layer execution',pass:capability.canExecuteFromAgentLayer&&capability.mode==='explicit_authorization'},
  {label:'Reviewed payload is present',pass:payloadReady},
 ]
 const ready=checks.every(x=>x.pass)
 return{ready,checks,reason:ready?'Ready for one bounded canonical action.':'Not ready. Keep this proposal in preparation/review; do not infer authorization or execution.'}
}
