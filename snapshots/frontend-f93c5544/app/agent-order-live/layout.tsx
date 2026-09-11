import ProfessionalHandoffContextPanel from '../components/ProfessionalHandoffContextPanel'
import ProfessionalWorkPrep from '../components/ProfessionalWorkPrep'
import ProfessionalAssistantActionDrafts from '../components/ProfessionalAssistantActionDrafts'
import ProfessionalAssistantNextBestAction from '../components/ProfessionalAssistantNextBestAction'
import OrderActivityPulse from '../components/OrderActivityPulse'
import OrderStallIntelligence from '../components/OrderStallIntelligence'
import AgentEscalationAdvisor from '../components/AgentEscalationAdvisor'
import AgentAuthorizedFollowup from '../components/AgentAuthorizedFollowup'
import AgentActionProposalLedger from '../components/AgentActionProposalLedger'
import AgentActionHistory from '../components/AgentActionHistory'
import AgentActionReadinessPanel from '../components/AgentActionReadinessPanel'
import AgentGoldenBoundaryStatus from '../components/AgentGoldenBoundaryStatus'
import AgentActionDecisionReceipt from '../components/AgentActionDecisionReceipt'
import AgentActionReconciliation from '../components/AgentActionReconciliation'

export default function AgentOrderLiveLayout({ children }: { children: React.ReactNode }) {
  return <><AgentGoldenBoundaryStatus role="agent" /><ProfessionalHandoffContextPanel /><ProfessionalAssistantNextBestAction /><AgentEscalationAdvisor role="agent" /><AgentAuthorizedFollowup role="agent" /><AgentActionReadinessPanel role="agent" /><AgentActionDecisionReceipt role="agent" /><AgentActionReconciliation role="agent" /><AgentActionHistory role="agent" /><AgentActionProposalLedger role="agent" /><OrderStallIntelligence role="agent" /><OrderActivityPulse role="agent" /><ProfessionalWorkPrep /><ProfessionalAssistantActionDrafts />{children}</>
}
