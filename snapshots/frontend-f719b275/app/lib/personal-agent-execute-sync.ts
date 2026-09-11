'use client'

import type { OrderSummary } from './order-api'
import {
  CURRENT_MATTER_KEY,
  LEGACY_WORKSPACE_KEY,
  MATTER_HISTORY_KEY,
  PersonalAgentMatter,
  readCurrentMatter,
  readMatterHistory,
  workspaceFromMatter,
} from './personal-agent-matter'

export function syncMatterExecution(order: OrderSummary) {
  if (typeof window === 'undefined') return null
  const current = readCurrentMatter()
  const history = readMatterHistory()
  const source = current?.knownFacts.service_order_id === order.id ? current : history.find(item => item.knownFacts.service_order_id === order.id)
  if (!source) return null
  const completed = order.stage === 'completed'
  const now = new Date().toISOString()
  const blueprint = source.blueprint.map(step => step.title === 'Execute' ? { ...step, status: completed ? 'completed' as const : 'active' as const } : step)
  const next: PersonalAgentMatter = {
    ...source,
    updatedAt: now,
    status: completed ? 'completed' : source.status,
    stage: completed ? 'completed' : 'execute',
    knownFacts: {
      ...source.knownFacts,
      service_order_id: order.id,
      service_order_stage: order.stage,
      service_order_updated_at: order.updatedAt || now,
      service_completed_confirmed: completed,
    },
    blueprint,
  }
  const nextHistory = [next, ...history.filter(item => item.id !== next.id)].sort((a,b)=>Date.parse(b.updatedAt)-Date.parse(a.updatedAt)).slice(0,50)
  window.localStorage.setItem(MATTER_HISTORY_KEY, JSON.stringify(nextHistory))
  if (current?.id === next.id) {
    window.localStorage.setItem(CURRENT_MATTER_KEY, JSON.stringify(next))
    window.localStorage.setItem(LEGACY_WORKSPACE_KEY, JSON.stringify(workspaceFromMatter(next)))
  }
  return next
}
