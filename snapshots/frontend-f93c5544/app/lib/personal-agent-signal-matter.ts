import { AgentSignal } from './personal-agent-signals'
import {
  CURRENT_MATTER_KEY,
  LEGACY_WORKSPACE_KEY,
  MATTER_RESTORE_EVENT,
  PersonalAgentMatter,
  saveMatterToHistory,
  workspaceFromMatter,
} from './personal-agent-matter'

function signalMatterId(signalId: string) {
  return `matter_signal_${signalId.replace(/[^a-zA-Z0-9_-]/g, '_')}`
}

function makeBlueprint(signal: AgentSignal) {
  return [
    { id: 1, title: 'Understand', status: 'completed' as const },
    { id: 2, title: 'Assess', status: 'active' as const },
    { id: 3, title: 'Plan', status: 'pending' as const },
    { id: 4, title: 'Connect', status: 'pending' as const },
    { id: 5, title: 'Execute', status: 'pending' as const },
  ]
}

function matterContext(signal: AgentSignal) {
  const parts = [
    signal.summary,
    signal.organization ? `Organization: ${signal.organization}` : '',
    signal.dueDate ? `Due date: ${signal.dueDate}` : '',
    signal.amount ? `Amount: ${signal.amount}` : '',
    signal.ownerActions?.length ? `Owner actions: ${signal.ownerActions.join('; ')}` : '',
    signal.agentCanDoNext?.length ? `Agent next steps: ${signal.agentCanDoNext.join('; ')}` : '',
    signal.missingInformation?.length ? `Missing information: ${signal.missingInformation.join('; ')}` : '',
  ].filter(Boolean)
  return parts.join('\n')
}

export function createMatterFromSignal(signal: AgentSignal): PersonalAgentMatter | null {
  if (typeof window === 'undefined' || !signal.analyzedAt || signal.analysisError) return null

  const now = new Date().toISOString()
  const matter: PersonalAgentMatter = {
    schemaVersion: 1,
    id: signalMatterId(signal.id),
    title: signal.suggestedMatterTitle || signal.title || 'Agent Matter',
    status: 'active',
    source: 'agent_signal',
    createdAt: now,
    updatedAt: now,
    sessionId: '',
    intent: signal.professionalCategory || null,
    subIntent: signal.documentType || null,
    stage: 'assess',
    knownFacts: {
      signal_id: signal.id,
      organization: signal.organization,
      due_date: signal.dueDate,
      amount: signal.amount,
      urgency: signal.urgency,
      risk_flags: signal.riskFlags || [],
      owner_actions: signal.ownerActions || [],
      agent_can_do_next: signal.agentCanDoNext || [],
      missing_information: signal.missingInformation || [],
      professional_needed: signal.professionalNeeded,
      professional_category: signal.professionalCategory || null,
      signal_reviewed_at: now,
    },
    thread: [
      {
        role: 'assistant',
        content: `I received and understood this Signal. I created a Matter so I can keep moving it forward.\n\n${matterContext(signal)}`,
        stage: 'assess',
      },
    ],
    blueprint: makeBlueprint(signal),
  }

  saveMatterToHistory(matter)
  window.localStorage.setItem(CURRENT_MATTER_KEY, JSON.stringify(matter))
  window.localStorage.setItem(LEGACY_WORKSPACE_KEY, JSON.stringify(workspaceFromMatter(matter)))
  window.dispatchEvent(new CustomEvent(MATTER_RESTORE_EVENT, { detail: { matterId: matter.id, sourceSignalId: signal.id } }))
  return matter
}
