'use client'

import { HandoffContext, orderApi } from './order-api'

export type PendingHandoffLike = {
  matterId?: string | null
  title?: string | null
  category?: string | null
  summary?: string | null
  organization?: string | null
  dueDate?: string | null
  amount?: string | null
  urgency?: string | null
  risks?: string[] | null
  ownerActions?: string[] | null
  agentNextSteps?: string[] | null
  missingInformation?: string[] | null
  reviewedAt?: string | null
  source?: string | null
  boundary?: string | null
}

function text(value: unknown) { return typeof value === 'string' ? value.trim() : '' }
function list(value: unknown) { return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && Boolean(item.trim())).slice(0, 20) : [] }

export function normalizeHandoff(input: PendingHandoffLike): HandoffContext {
  const urgency = ['low','normal','high','urgent'].includes(text(input.urgency)) ? text(input.urgency) as HandoffContext['urgency'] : 'normal'
  return {
    matterId: text(input.matterId),
    title: text(input.title),
    category: text(input.category),
    summary: text(input.summary),
    organization: text(input.organization) || null,
    dueDate: text(input.dueDate) || null,
    amount: text(input.amount) || null,
    urgency,
    risks: list(input.risks),
    ownerActions: list(input.ownerActions),
    agentNextSteps: list(input.agentNextSteps),
    missingInformation: list(input.missingInformation),
    reviewedAt: text(input.reviewedAt) || new Date().toISOString(),
    source: 'customer_butler',
  }
}

export async function ensureStructuredHandoff(orderId: string, input: PendingHandoffLike | null, token: string) {
  if (!input?.matterId || !input?.title) return null
  const payload = normalizeHandoff(input)
  return orderApi.saveHandoffContext(orderId, payload, token)
}
