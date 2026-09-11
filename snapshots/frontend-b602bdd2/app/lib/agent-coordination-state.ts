import type { DeliveryPackage, OrderSummary, SupplementRequest } from './order-api'

export type CoordinationOwner='customer'|'professional'|'system'|'none'
export type CoordinationState={
  phase:'connect'|'estimate'|'payment'|'information'|'execution'|'delivery'|'confirmation'|'completed'
  owner:CoordinationOwner
  title:string
  reason:string
  customerView:string
  professionalView:string
  completionAllowed:boolean
}

export function deriveCoordinationState(order:OrderSummary,supplement?:SupplementRequest|null,delivery?:DeliveryPackage|null):CoordinationState{
  const pending=(supplement?.items||[]).filter(x=>x.required&&!['answered','complete','skipped'].includes(x.status))
  if(order.stage==='completed')return{phase:'completed',owner:'none',title:'Matter completed',reason:'The customer-confirmed order state is completed.',customerView:'You confirmed completion. Your AI Butler can close this Matter.',professionalView:'The customer confirmed completion. No further execution action is required.',completionAllowed:true}
  if(!order.matched)return{phase:'connect',owner:'system',title:'Matching a licensed professional',reason:'The service order has not been matched yet.',customerView:'I’m still working on the connection. You do not need to manage the professional side yourself.',professionalView:'This order is not yet assigned to a professional.',completionAllowed:false}
  if(order.stage==='estimate'&&!order.estimate)return{phase:'estimate',owner:'professional',title:'Professional estimate needed',reason:'The order is matched, but no professional estimate is available yet.',customerView:'The professional is reviewing the Matter. I’m waiting for the scope and fee.',professionalView:'Prepare the professional service scope and fee after reviewing the customer-reviewed context.',completionAllowed:false}
  if(order.stage==='estimate'&&order.estimate)return{phase:'estimate',owner:'customer',title:'Customer estimate decision',reason:'The estimate is ready and requires the customer’s decision.',customerView:'Review the scope and fee and decide whether to accept.',professionalView:'Wait for the customer to accept or decline the estimate. Do not treat the estimate as authorization.',completionAllowed:false}
  if(order.stage==='accepted')return{phase:'payment',owner:'customer',title:'Verified service payment needed',reason:'The service scope is accepted but the order has not reached verified paid state.',customerView:'Complete the professional service payment when you are ready to proceed.',professionalView:'Wait for verified payment before beginning paid execution.',completionAllowed:false}
  if(pending.length)return{phase:'information',owner:'customer',title:'Customer information needed',reason:`${pending.length} required item${pending.length===1?' is':'s are'} still outstanding.`,customerView:`Provide the requested information: ${pending.slice(0,4).map(x=>x.label).join('; ')}.`,professionalView:'Wait for the required customer information, then review it before continuing.',completionAllowed:false}
  if(order.stage==='paid')return{phase:'execution',owner:'professional',title:'Professional service ready to start',reason:'Verified professional service payment is present and no customer information blocker is visible.',customerView:'Payment is confirmed. I’m watching for the professional to start the work.',professionalView:'Begin the accepted professional service scope.',completionAllowed:false}
  if(order.stage==='processing')return{phase:'execution',owner:'professional',title:'Professional work in progress',reason:'The order is actively processing and no customer blocker is visible.',customerView:'The professional is working. I’m continuing to track the Matter.',professionalView:'Continue the approved work. Use a supplement request if new customer information becomes necessary.',completionAllowed:false}
  if(order.stage==='waiting_customer')return{phase:'information',owner:'customer',title:'Waiting on customer response',reason:'The canonical order state is waiting_customer.',customerView:'Check the professional’s requested information or decision and respond so the work can continue.',professionalView:'Wait for the customer response. Do not mark the order complete while the customer blocker remains.',completionAllowed:false}
  if(order.stage==='delivered'||delivery?.status==='submitted')return{phase:'confirmation',owner:'customer',title:'Customer review and confirmation',reason:'Professional deliverables are submitted, but delivery alone is not completion.',customerView:'Review the deliverables and confirm completion only when you are satisfied.',professionalView:'Wait for customer confirmation. Do not close the Matter on the customer’s behalf.',completionAllowed:false}
  return{phase:'execution',owner:'system',title:'Tracking canonical order state',reason:`The order is currently ${order.stage}.`,customerView:'I’m tracking the real service order and will surface the next required action.',professionalView:'Use the canonical order workflow as the source of truth for the next action.',completionAllowed:false}
}
