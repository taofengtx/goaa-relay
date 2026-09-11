import {orderApi,type SupplementType} from './order-api'
import {canAgentLayerExecute} from './agent-action-capabilities'
import {runCanonicalActionPreflight} from './agent-action-canonical-preflight'
import {assertPostGoldenAgentAction} from './golden-flow-boundary'
import {checkProposalIntegrity} from './agent-action-integrity'
import type {AgentActionProposal} from './agent-action-proposals'

type InfoItem={label:string;type:SupplementType;required:boolean}
export type AgentActionExecutionReceipt={kind:'message'|'supplement';id:string}
const SUPPLEMENT_TYPES=new Set<SupplementType>(['text','date','amount','choice','image','pdf','file'])
function informationItems(payload:Record<string,unknown>):InfoItem[]{
 const raw=payload.items
 if(!Array.isArray(raw)||!raw.length||raw.length>20)return[]
 const items:InfoItem[]=[]
 for(const value of raw){
  if(!value||typeof value!=='object')return[]
  const item=value as Record<string,unknown>
  const label=typeof item.label==='string'?item.label.trim():''
  const rawType=typeof item.type==='string'?item.type:'text'
  if(!label||label.length>300||!SUPPLEMENT_TYPES.has(rawType as SupplementType))return[]
  items.push({label,type:rawType as SupplementType,required:item.required!==false})
 }
 return items
}

export async function executeApprovedAgentAction(proposal:AgentActionProposal,token:string):Promise<AgentActionExecutionReceipt>{
 if(!token)throw new Error('Authorization token is required')
 if(proposal.status!=='executing')throw new Error('Proposal must be in executing state before canonical execution')
 assertPostGoldenAgentAction(proposal.actionType)
 const integrity=checkProposalIntegrity(proposal)
 if(!integrity.pass)throw new Error(`Agent proposal integrity check failed: ${integrity.checks.filter(x=>!x.pass).map(x=>x.label).join('; ')}`)
 if(!canAgentLayerExecute(proposal.actionType))throw new Error(`Action ${proposal.actionType} is not executable from the Agent layer`)
 const preflight=await runCanonicalActionPreflight(proposal,token)
 if(!preflight.pass)throw new Error(`Canonical preflight failed: ${preflight.checks.filter(x=>!x.pass).map(x=>x.label).join('; ')}`)
 if(proposal.actionType==='send_message'){
 const message=typeof proposal.payloadPreview.message==='string'?proposal.payloadPreview.message.trim():''
 if(!message)throw new Error('Reviewed message is required')
 const result=await orderApi.sendMessage(proposal.orderId,message,token)
  const id=typeof result?.id==='string'?result.id.trim():''
  if(!id)throw new Error('Canonical message API did not return a receipt id')
  return{kind:'message',id}
 }
 if(proposal.actionType==='request_information'){
 const items=informationItems(proposal.payloadPreview)
 if(!items.length)throw new Error('Reviewed information-request items are required')
 const result=await orderApi.createSupplement(proposal.orderId,items,token)
  const id=typeof result?.id==='string'?result.id.trim():''
  if(!id)throw new Error('Canonical supplement API did not return a receipt id')
  return{kind:'supplement',id}
 }
 throw new Error(`No bounded executor exists for ${proposal.actionType}`)
}
