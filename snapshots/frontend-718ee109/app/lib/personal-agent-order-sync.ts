'use client'

import {
  CURRENT_MATTER_KEY,
  LEGACY_WORKSPACE_KEY,
  MATTER_HISTORY_KEY,
  PersonalAgentMatter,
  readCurrentMatter,
  readMatterHistory,
  workspaceFromMatter,
} from './personal-agent-matter'

export function syncMatterMatched(matterId: string, orderId: string) {
  if (typeof window === 'undefined' || !matterId) return null
  const current = readCurrentMatter()
  const history = readMatterHistory()
  const source = current?.id === matterId ? current : history.find((item) => item.id === matterId)
  if (!source) return null
  const now = new Date().toISOString()
  const knownFacts = { ...source.knownFacts, service_order_id: orderId, professional_handoff_confirmed: true }
  const blueprint = source.blueprint.map((step) => {
    if (step.title === 'Connect') return { ...step, status: 'completed' as const }
    if (step.title === 'Execute') return { ...step, status: 'active' as const }
    return step
  })
  const next: PersonalAgentMatter = { ...source, updatedAt: now, status: 'professional_handoff', stage: 'execute', knownFacts, blueprint }
  const nextHistory = [next, ...history.filter((item) => item.id !== matterId)].sort((a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt)).slice(0, 50)
  window.localStorage.setItem(MATTER_HISTORY_KEY, JSON.stringify(nextHistory))
  if (current?.id === matterId) {
    window.localStorage.setItem(CURRENT_MATTER_KEY, JSON.stringify(next))
    window.localStorage.setItem(LEGACY_WORKSPACE_KEY, JSON.stringify(workspaceFromMatter(next)))
  }
  return next
}
