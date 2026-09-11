import ButlerExecutionTracker from '../components/ButlerExecutionTracker'
import CustomerRecoveryNav from '../components/CustomerRecoveryNav'
import ButlerBlockerDetector from '../components/ButlerBlockerDetector'
import OrderActivityPulse from '../components/OrderActivityPulse'
import OrderStallIntelligence from '../components/OrderStallIntelligence'
import AgentEscalationAdvisor from '../components/AgentEscalationAdvisor'
import AgentAuthorizedFollowup from '../components/AgentAuthorizedFollowup'
import AgentActionHistory from '../components/AgentActionHistory'
import AgentActionReadinessPanel from '../components/AgentActionReadinessPanel'
import AgentGoldenBoundaryStatus from '../components/AgentGoldenBoundaryStatus'
import AgentActionDecisionReceipt from '../components/AgentActionDecisionReceipt'
import AgentActionReconciliation from '../components/AgentActionReconciliation'

export default function CustomerOrderLiveLayout({ children }: { children: React.ReactNode }) {
  return <><CustomerRecoveryNav /><AgentGoldenBoundaryStatus role="customer" /><ButlerExecutionTracker /><ButlerBlockerDetector /><AgentEscalationAdvisor role="customer" /><AgentAuthorizedFollowup role="customer" /><AgentActionReadinessPanel role="customer" /><AgentActionDecisionReceipt role="customer" /><AgentActionReconciliation role="customer" /><AgentActionHistory role="customer" /><OrderStallIntelligence role="customer" /><OrderActivityPulse role="customer" />{children}</>
}
