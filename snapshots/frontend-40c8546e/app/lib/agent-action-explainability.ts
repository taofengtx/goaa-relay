import {agentActionCapability} from './agent-action-capabilities'
import {isPostGoldenAgentAction} from './golden-flow-boundary'
import type {AgentActionProposal} from './agent-action-proposals'

export type AgentActionDecisionExplanation={
 headline:string
 why:string
 controlledBy:string
 canonicalPath:string
 goldenBoundary:string
 lifecycle:string
 nextStep:string
 willHappen:string[]
 willNotHappen:string[]
}

export function explainAgentActionDecision(proposal:AgentActionProposal):AgentActionDecisionExplanation{
 const capability=agentActionCapability(proposal.actionType)
 const controlledBy=proposal.authorizer==='customer'?'Customer':'Licensed professional'
 const lifecycle=proposal.status==='proposed'?'Waiting for explicit human authorization.'
  :proposal.status==='approved'?'Authorized, but not yet in canonical execution.'
  :proposal.status==='executing'?'Executing one bounded canonical action.'
  :proposal.status==='executed'?'Canonical action returned successfully; local proposal is recorded as executed.'
  :proposal.status==='failed'?'Canonical action did not complete successfully. This proposal is terminal; retry requires a new proposal and new authorization.'
  :'Cancelled before execution. No canonical business action is implied.'
 const nextStep=proposal.status==='proposed'?`The ${controlledBy.toLowerCase()} reviews the proposal and decides whether to approve it.`
  :proposal.status==='approved'?'Run the bounded executor only if readiness checks still pass.'
  :proposal.status==='executing'?'Wait for the real Order Engine result; do not infer success.'
  :proposal.status==='failed'?'Prepare a new retry proposal only if the human wants to try again.'
  :'No additional action is implied by this proposal.'
 return{
  headline:proposal.title,
  why:proposal.rationale||'No additional rationale was recorded.',
  controlledBy,
  canonicalPath:capability.canonicalPath,
  goldenBoundary:isPostGoldenAgentAction(proposal.actionType)?'Allowed only as a Post-Golden overlay action. Golden business state is not replaced.':'Protected Golden action — Agent Layer execution is blocked.',
  lifecycle,
  nextStep,
  willHappen:proposal.willHappen,
  willNotHappen:proposal.willNotHappen,
 }
}
