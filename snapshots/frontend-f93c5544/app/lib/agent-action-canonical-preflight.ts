import {orderApi} from './order-api'
import type {AgentActionProposal} from './agent-action-proposals'

export type CanonicalActionPreflight={pass:boolean;checks:{label:string;pass:boolean}[];reason:string}

function proposalStage(proposal:AgentActionProposal){
 if(proposal.actionType!=='send_message'||!proposal.scopeKey)return''
 const value=proposal.scopeKey.split(':')[0]||''
 return ['estimate','accepted','paid','processing','waiting_customer','delivered','completed'].includes(value)?value:''
}

export async function runCanonicalActionPreflight(proposal:AgentActionProposal,token:string):Promise<CanonicalActionPreflight>{
 if(!token)return{pass:false,checks:[{label:'Canonical authorization token is present',pass:false}],reason:'Canonical authorization is missing.'}
 const order=await orderApi.getOrder(proposal.orderId,token)
 const checks:{label:string;pass:boolean}[]=[
  {label:'Canonical order still exists and is readable by the authorizer',pass:Boolean(order?.id===proposal.orderId)},
 ]
 if(proposal.actionType==='send_message'){
  const expectedStage=proposalStage(proposal)
  if(expectedStage)checks.push({label:`Order stage is still ${expectedStage}`,pass:order.stage===expectedStage})
  checks.push({label:'Order is not already completed',pass:order.stage!=='completed'})
 }
 if(proposal.actionType==='request_information'){
  let supplement=null
  let supplementReadable=true
  try{supplement=await orderApi.getSupplement(proposal.orderId,token)}catch{supplementReadable=false}
  checks.push({label:'Canonical supplement state is readable',pass:supplementReadable})
  checks.push({label:'No canonical supplement request already exists',pass:supplementReadable&&!supplement})
  checks.push({label:'Order is not already completed',pass:order.stage!=='completed'})
 }
 const pass=checks.every(x=>x.pass)
 return{pass,checks,reason:pass?'Canonical state still matches the reviewed proposal.':'Canonical state changed or could not be verified after the proposal was prepared. Review again before any external action.'}
}
