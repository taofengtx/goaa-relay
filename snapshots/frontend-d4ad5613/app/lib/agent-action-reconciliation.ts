import {orderApi} from './order-api'
import {recordCanonicalVerification,type AgentActionProposal,type CanonicalVerificationState} from './agent-action-proposals'

export type ReconciliationResult={state:CanonicalVerificationState;reason:string}

export async function reconcileExecutedAgentAction(proposal:AgentActionProposal,token:string):Promise<ReconciliationResult>{
 if(proposal.status!=='executed'||!proposal.canonicalResultId||!proposal.canonicalResultKind)return{state:'unverified',reason:'No canonical execution receipt is available to verify.'}
 if(!token)return{state:'unavailable',reason:'Canonical authorization is unavailable.'}
 try{
  if(proposal.canonicalResultKind==='message'){
   const messages=await orderApi.getMessages(proposal.orderId,token)
   const found=messages.some(item=>item.id===proposal.canonicalResultId)
   const state:CanonicalVerificationState=found?'verified':'not_found'
   recordCanonicalVerification(proposal.id,state)
   return{state,reason:found?'Canonical message still exists in the Order Engine.':'The locally recorded message receipt was not found in the canonical Order Engine response.'}
  }
  const supplement=await orderApi.getSupplement(proposal.orderId,token)
  const found=Boolean(supplement&&supplement.id===proposal.canonicalResultId)
  const state:CanonicalVerificationState=found?'verified':'not_found'
  recordCanonicalVerification(proposal.id,state)
  return{state,reason:found?'Canonical supplement still exists in the Order Engine.':'The locally recorded supplement receipt was not found in the canonical Order Engine response.'}
 }catch{
  recordCanonicalVerification(proposal.id,'unavailable')
  return{state:'unavailable',reason:'Canonical receipt could not be verified right now. No business state was changed.'}
 }
}
