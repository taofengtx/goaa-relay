'use client'

import { orderApi } from './order-api'
import { runtimeToken } from './order-runtime'
import { PersonalAgentMatter } from './personal-agent-matter'

const ACTIVE_ORDER_KEY = 'goaa_active_order_id'
const MATTER_ORDER_LINK_KEY = 'goaa_matter_order_links_v1'

export type MatterOrderLink = { matterId: string; orderId: string; createdAt: string; category?: string }

function readLinks(): MatterOrderLink[] {
  if (typeof window === 'undefined') return []
  try { const value = JSON.parse(window.localStorage.getItem(MATTER_ORDER_LINK_KEY) || '[]'); return Array.isArray(value) ? value : [] } catch { return [] }
}

export function getMatterOrderLink(matterId: string) { return readLinks().find((item) => item.matterId === matterId) || null }

function saveLink(link: MatterOrderLink) {
  if (typeof window === 'undefined') return
  const next = [link, ...readLinks().filter((item) => item.matterId !== link.matterId)].slice(0, 50)
  window.localStorage.setItem(MATTER_ORDER_LINK_KEY, JSON.stringify(next))
  window.localStorage.setItem(ACTIVE_ORDER_KEY, link.orderId)
}

function text(value: unknown) { return typeof value === 'string' ? value.trim() : '' }

export async function createCanonicalOrderFromMatter(matter: PersonalAgentMatter) {
  const existing = getMatterOrderLink(matter.id)
  if (existing) return existing
  const category = text(matter.knownFacts.professional_category) || text(matter.subIntent) || text(matter.intent) || undefined
  const organization = text(matter.knownFacts.organization)
  const dueDate = text(matter.knownFacts.due_date)
  const summary = text(matter.knownFacts.summary)
  const need = [matter.title, summary, organization ? `Organization: ${organization}` : '', dueDate ? `Due date: ${dueDate}` : ''].filter(Boolean).join('\n')
  const token = runtimeToken('customer')
  const order = await orderApi.createOrder({ need, category, serviceTitle: matter.title }, token || undefined)
  const link = { matterId: matter.id, orderId: order.id, createdAt: new Date().toISOString(), category }
  saveLink(link)
  return link
}

export async function startCanonicalConnectCheckout(matter: PersonalAgentMatter) {
  const link = await createCanonicalOrderFromMatter(matter)
  const token = runtimeToken('customer')
  const checkout = await orderApi.createConnectCheckout(link.orderId, token || undefined)
  return { link, checkout }
}
