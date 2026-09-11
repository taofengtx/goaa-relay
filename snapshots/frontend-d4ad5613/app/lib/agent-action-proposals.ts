export type AgentActionType='send_message'|'request_information'|'start_service'|'prepare_delivery'|'connect_professional'
export type AgentActionStatus='proposed'|'approved'|'executing'|'executed'|'failed'|'cancelled'|'superseded'
export type AgentAuthorizer='customer'|'professional'
export type CanonicalVerificationState='unverified'|'verified'|'not_found'|'unavailable'
export type AgentActionProposal={
 id:string
 orderId:string
 actionType:AgentActionType
 authorizer:AgentAuthorizer
 scopeKey?:string
 retryOf?:string
 title:string
 rationale:string
 willHappen:string[]
 willNotHappen:string[]
 payloadPreview:Record<string,unknown>
 status:AgentActionStatus
 createdAt:string
 updatedAt?:string
 approvedAt?:string
 executedAt?:string
 failedAt?:string
 cancelledAt?:string
 supersededAt?:string
 failureMessage?:string
 canonicalResultKind?:'message'|'supplement'
 canonicalResultId?:string
 canonicalVerificationState?:CanonicalVerificationState
 canonicalVerifiedAt?:string
}
type AgentActionTransitionPatch=Partial<Pick<AgentActionProposal,'payloadPreview'|'failureMessage'|'canonicalResultKind'|'canonicalResultId'>>
const KEY='goaa_agent_action_proposals_v1'
const TRANSITIONS:Record<AgentActionStatus,AgentActionStatus[]>={proposed:['approved','cancelled','superseded'],approved:['executing','cancelled','superseded'],executing:['executed','failed'],executed:[],failed:[],cancelled:[],superseded:[]}
const ACTION_TYPES=new Set<AgentActionType>(['send_message','request_information','start_service','prepare_delivery','connect_professional'])
const ACTION_STATUSES=new Set<AgentActionStatus>(['proposed','approved','executing','executed','failed','cancelled','superseded'])
const ACTION_AUTHORIZERS=new Set<AgentAuthorizer>(['customer','professional'])
const VERIFICATION_STATES=new Set<CanonicalVerificationState>(['unverified','verified','not_found','unavailable'])
const CANONICAL_RESULT_KINDS:Partial<Record<AgentActionType,'message'|'supplement'>>={send_message:'message',request_information:'supplement'}
function isProposalRecord(value:unknown):value is AgentActionProposal{
 if(!value||typeof value!=='object'||Array.isArray(value))return false
 const item=value as Record<string,unknown>
 if(typeof item.id!=='string'||!item.id||item.id.length>500)return false
 if(typeof item.orderId!=='string'||!item.orderId||item.orderId.length>200)return false
 if(typeof item.actionType!=='string'||!ACTION_TYPES.has(item.actionType as AgentActionType))return false
 if(typeof item.authorizer!=='string'||!ACTION_AUTHORIZERS.has(item.authorizer as AgentAuthorizer))return false
 if(typeof item.status!=='string'||!ACTION_STATUSES.has(item.status as AgentActionStatus))return false
 if(typeof item.title!=='string'||!item.title.trim()||item.title.length>300)return false
 if(typeof item.rationale!=='string'||item.rationale.length>2000)return false
 if(typeof item.createdAt!=='string'||!item.createdAt)return false
 if(item.scopeKey!==undefined&&(typeof item.scopeKey!=='string'||item.scopeKey.length>200))return false
 if(item.retryOf!==undefined&&typeof item.retryOf!=='string')return false
 if(!Array.isArray(item.willHappen)||!Array.isArray(item.willNotHappen)||item.willHappen.length>20||item.willNotHappen.length>20)return false
 if([...item.willHappen,...item.willNotHappen].some(entry=>typeof entry!=='string'||entry.length>500))return false
 if(!item.payloadPreview||typeof item.payloadPreview!=='object'||Array.isArray(item.payloadPreview)||JSON.stringify(item.payloadPreview).length>8192)return false
 const hasCanonicalResultKind=item.canonicalResultKind!==undefined
 const hasCanonicalResultId=item.canonicalResultId!==undefined
 if(hasCanonicalResultKind!==hasCanonicalResultId)return false
 if(hasCanonicalResultKind&&!['message','supplement'].includes(String(item.canonicalResultKind)))return false
 if(hasCanonicalResultId&&(typeof item.canonicalResultId!=='string'||!item.canonicalResultId.trim()||item.canonicalResultId.length>500))return false
 if(item.status==='executed'&&!hasCanonicalResultId)return false
 if(item.status!=='executed'&&hasCanonicalResultId)return false
 if(item.status==='executed'&&CANONICAL_RESULT_KINDS[item.actionType as AgentActionType]!==item.canonicalResultKind)return false
 if(item.canonicalVerificationState!==undefined&&(typeof item.canonicalVerificationState!=='string'||!VERIFICATION_STATES.has(item.canonicalVerificationState as CanonicalVerificationState)))return false
 return true
}
function all():AgentActionProposal[]{if(typeof window==='undefined')return[];try{const raw=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(raw)?raw.filter(isProposalRecord):[]}catch{return[]}}
function write(items:AgentActionProposal[]){if(typeof window!=='undefined'){localStorage.setItem(KEY,JSON.stringify(items.slice(-100)));window.dispatchEvent(new Event('goaa-agent-action-proposals-updated'))}}
function assertBoundedInput(input:Omit<AgentActionProposal,'id'|'status'|'createdAt'|'updatedAt'>){if(!input.orderId||input.orderId.length>200)throw new Error('Invalid proposal order id');if(!input.title.trim()||input.title.length>300)throw new Error('Proposal title must be 1-300 characters');if(input.rationale.length>2000)throw new Error('Proposal rationale is too long');if((input.scopeKey||'').length>200)throw new Error('Proposal scope key is too long');if(input.willHappen.length>20||input.willNotHappen.length>20)throw new Error('Proposal disclosure arrays are too large');if([...input.willHappen,...input.willNotHappen].some(v=>typeof v!=='string'||v.length>500))throw new Error('Proposal disclosure item is invalid');if(JSON.stringify(input.payloadPreview||{}).length>8192)throw new Error('Proposal payload preview is too large')}
export function proposalId(orderId:string,actionType:AgentActionType){return `${orderId}:${actionType}:${Date.now()}:${Math.random().toString(36).slice(2,8)}`}
export function createActionProposal(input:Omit<AgentActionProposal,'id'|'status'|'createdAt'|'updatedAt'>){assertBoundedInput(input);const now=new Date().toISOString();const proposal:AgentActionProposal={...input,id:proposalId(input.orderId,input.actionType),status:'proposed',createdAt:now,updatedAt:now};write([...all(),proposal]);return proposal}
export function ensureActionProposal(input:Omit<AgentActionProposal,'id'|'status'|'createdAt'|'updatedAt'>){assertBoundedInput(input);const items=all();const existing=items.filter(item=>item.orderId===input.orderId&&item.actionType===input.actionType&&item.authorizer===input.authorizer&&item.scopeKey===input.scopeKey&&['proposed','approved','executing'].includes(item.status)).sort((a,b)=>b.createdAt.localeCompare(a.createdAt))[0];if(existing)return existing;const now=new Date().toISOString();let changed=false;const next=items.map(item=>{const stale=item.orderId===input.orderId&&item.actionType===input.actionType&&item.authorizer===input.authorizer&&item.scopeKey!==input.scopeKey&&['proposed','approved'].includes(item.status);if(!stale)return item;changed=true;return{...item,status:'superseded' as AgentActionStatus,supersededAt:now,updatedAt:now}});if(changed)write(next);return createActionProposal(input)}
function updateActionProposal(id:string,patch:Partial<AgentActionProposal>){const items=all();const next=items.map(item=>item.id===id?{...item,...patch,updatedAt:new Date().toISOString()}:item);write(next);return next.find(item=>item.id===id)||null}
export function transitionActionProposal(id:string,status:AgentActionStatus,patch:AgentActionTransitionPatch={}){
 const current=all().find(item=>item.id===id)
 if(!current)return null
 if(!TRANSITIONS[current.status].includes(status))return current
 const allowedPatch:AgentActionTransitionPatch={}
 if(status==='approved'&&patch.payloadPreview!==undefined){
  if(!patch.payloadPreview||typeof patch.payloadPreview!=='object'||Array.isArray(patch.payloadPreview)||JSON.stringify(patch.payloadPreview).length>8192)return current
  allowedPatch.payloadPreview=patch.payloadPreview
 }
 if(status==='failed'&&patch.failureMessage!==undefined){
  if(typeof patch.failureMessage!=='string'||patch.failureMessage.length>2000)return current
  allowedPatch.failureMessage=patch.failureMessage
 }
 if(status==='executed'){
  const resultId=typeof patch.canonicalResultId==='string'?patch.canonicalResultId.trim():''
  const resultKind=CANONICAL_RESULT_KINDS[current.actionType]
  if(!resultId||resultId.length>500||!resultKind||resultKind!==patch.canonicalResultKind)return current
  allowedPatch.canonicalResultId=resultId
  allowedPatch.canonicalResultKind=resultKind
 }
 const now=new Date().toISOString()
 const timestamps=status==='approved'?{approvedAt:now}:status==='executed'?{executedAt:now}:status==='failed'?{failedAt:now}:status==='cancelled'?{cancelledAt:now}:status==='superseded'?{supersededAt:now}:{}
 return updateActionProposal(id,{...allowedPatch,...timestamps,status})
}
export function recordCanonicalVerification(id:string,state:CanonicalVerificationState){const current=all().find(item=>item.id===id);if(!current||current.status!=='executed'||!current.canonicalResultId)return current||null;return updateActionProposal(id,{canonicalVerificationState:state,canonicalVerifiedAt:new Date().toISOString()})}
export function cancelActionProposal(id:string){return transitionActionProposal(id,'cancelled')}
export function prepareActionRetry(id:string){const source=all().find(item=>item.id===id);if(!source||source.status!=='failed')return null;const {id:sourceId,status,createdAt,updatedAt,approvedAt,executedAt,failedAt,cancelledAt,supersededAt,failureMessage,canonicalResultKind,canonicalResultId,canonicalVerificationState,canonicalVerifiedAt,...rest}=source;return createActionProposal({...rest,retryOf:sourceId})}
export function listActionProposals(orderId:string,authorizer?:AgentAuthorizer){return all().filter(item=>item.orderId===orderId&&(!authorizer||item.authorizer===authorizer)).sort((a,b)=>b.createdAt.localeCompare(a.createdAt))}
export function latestActionProposal(orderId:string,actionType:AgentActionType,authorizer:AgentAuthorizer){return listActionProposals(orderId,authorizer).find(item=>item.actionType===actionType)||null}
export function proposalStatusLabel(status:AgentActionStatus){return({proposed:'Proposed',approved:'Approved',executing:'Executing',executed:'Executed',failed:'Failed',cancelled:'Cancelled',superseded:'Superseded'} as Record<AgentActionStatus,string>)[status]}
