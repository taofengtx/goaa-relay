import {
  CURRENT_MATTER_KEY,
  LEGACY_WORKSPACE_KEY,
  PersonalAgentMatter,
  readCurrentMatter,
  saveMatterToHistory,
  workspaceFromMatter,
} from './personal-agent-matter'

export type MatterProgressGate = {
  canAdvance: boolean
  from: string
  to: string | null
  reason: string
  needsOwner: boolean
  needsProfessional: boolean
}

function list(value: unknown) {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && Boolean(item.trim())) : []
}

function activeStep(matter: PersonalAgentMatter) {
  return matter.blueprint.find((step) => step.status === 'active') || null
}

export function evaluateMatterProgress(matter: PersonalAgentMatter): MatterProgressGate {
  const active = activeStep(matter)
  const from = active?.title || matter.stage || 'Assess'
  const missing = list(matter.knownFacts.missing_information)
  const ownerActions = list(matter.knownFacts.owner_actions)
  const professionalNeeded = matter.knownFacts.professional_needed === true

  if (from === 'Assess') {
    if (missing.length > 0) return { canAdvance: false, from, to: 'Plan', reason: 'Missing information still blocks a safe plan.', needsOwner: ownerActions.length > 0 || missing.length > 0, needsProfessional: professionalNeeded }
    if (ownerActions.length > 0) return { canAdvance: false, from, to: 'Plan', reason: 'Owner input or approval is still needed before planning.', needsOwner: true, needsProfessional: professionalNeeded }
    return { canAdvance: true, from, to: 'Plan', reason: 'Assessment has enough confirmed context to build the next-step plan.', needsOwner: false, needsProfessional: professionalNeeded }
  }

  if (from === 'Plan') {
    if (professionalNeeded) return { canAdvance: true, from, to: 'Connect', reason: 'The plan requires licensed professional execution.', needsOwner: false, needsProfessional: true }
    return { canAdvance: true, from, to: 'Execute', reason: 'No professional handoff is required; the Butler can continue toward execution.', needsOwner: false, needsProfessional: false }
  }

  if (from === 'Connect') return { canAdvance: false, from, to: 'Execute', reason: 'Connection must be explicitly confirmed through the professional handoff flow.', needsOwner: true, needsProfessional: true }
  if (from === 'Execute') return { canAdvance: false, from, to: null, reason: 'Execution stays active until a real completion signal is recorded.', needsOwner: false, needsProfessional: professionalNeeded }
  return { canAdvance: false, from, to: null, reason: 'This Matter has no safe automatic progression available.', needsOwner: false, needsProfessional: professionalNeeded }
}

export function advanceCurrentMatter(): PersonalAgentMatter | null {
  if (typeof window === 'undefined') return null
  const matter = readCurrentMatter()
  if (!matter || matter.source !== 'agent_signal') return null
  const gate = evaluateMatterProgress(matter)
  if (!gate.canAdvance || !gate.to) return null

  const nextTitle = gate.to
  const now = new Date().toISOString()
  const blueprint = matter.blueprint.map((step) => {
    if (step.title === gate.from) return { ...step, status: 'completed' as const }
    if (step.title === nextTitle) return { ...step, status: 'active' as const }
    if (gate.from === 'Plan' && nextTitle === 'Execute' && step.title === 'Connect') return { ...step, status: 'completed' as const }
    return step
  })

  const next: PersonalAgentMatter = {
    ...matter,
    updatedAt: now,
    stage: nextTitle.toLowerCase(),
    status: nextTitle === 'Connect' ? 'professional_handoff' : matter.status,
    blueprint,
  }
  window.localStorage.setItem(CURRENT_MATTER_KEY, JSON.stringify(next))
  window.localStorage.setItem(LEGACY_WORKSPACE_KEY, JSON.stringify(workspaceFromMatter(next)))
  saveMatterToHistory(next)
  return next
}
