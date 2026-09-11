import type {AgentActionProposal,AgentActionStatus,AgentAuthorizer,CanonicalVerificationState} from './agent-action-proposals'

/**
 * Frontend-side contract for a future persistent server ledger.
 * This does not call a new backend route and does not change Golden Flow.
 * It exists so local proposal semantics remain stable before any approved backend implementation.
 */
export type AgentActionLedgerRecord={
 proposalId:string
 orderId:string
 actionType:AgentActionProposal['actionType']
 authorizer:AgentAuthorizer
 status:AgentActionStatus
 version:number
 scopeKey?:string
 retryOf?:string
 title:string
 rationale:string
 willHappen:string[]
 willNotHappen:string[]
 payloadPreview:Record<string,unknown>
 canonicalResultKind?:AgentActionProposal['canonicalResultKind']
 canonicalResultId?:string
 canonicalVerificationState?:CanonicalVerificationState
 createdAt:string
 updatedAt?:string
 approvedAt?:string
 executedAt?:string
 failedAt?:string
 cancelledAt?:string
 supersededAt?:string
 failureMessage?:string
}

export function toLedgerRecord(proposal:AgentActionProposal):AgentActionLedgerRecord{return{
 proposalId:proposal.id,orderId:proposal.orderId,actionType:proposal.actionType,authorizer:proposal.authorizer,status:proposal.status,version:1,scopeKey:proposal.scopeKey,retryOf:proposal.retryOf,title:proposal.title,rationale:proposal.rationale,willHappen:proposal.willHappen,willNotHappen:proposal.willNotHappen,payloadPreview:proposal.payloadPreview,canonicalResultKind:proposal.canonicalResultKind,canonicalResultId:proposal.canonicalResultId,canonicalVerificationState:proposal.canonicalVerificationState,createdAt:proposal.createdAt,updatedAt:proposal.updatedAt,approvedAt:proposal.approvedAt,executedAt:proposal.executedAt,failedAt:proposal.failedAt,cancelledAt:proposal.cancelledAt,supersededAt:proposal.supersededAt,failureMessage:proposal.failureMessage}}

export const SERVER_LEDGER_NON_NEGOTIABLES=[
 'The client may not directly claim executed.',
 'Executed must be correlated to a successful canonical business action.',
 'Failed, cancelled, superseded, and executed records are terminal.',
 'Retry creates a new proposal and requires new authorization.',
 'Customer and professional authorizations remain role-isolated.',
 'No generic execute-anything endpoint may be introduced.',
 'Golden Flow business state remains canonical and unchanged.',
] as const
