import type { OrderSummary } from './order-api'
import type { PersonalAgentMatter } from './personal-agent-matter'

export type MatterCategory = 'conversation' | 'organizing' | 'connecting' | 'completed'

export type ButlerMatterRow = {
  id: string
  title: string
  group: 'active' | 'completed'
  category: MatterCategory
  status: string
  updatedAt: string
  matter?: PersonalAgentMatter
  order?: OrderSummary
  linkedOrderId?: string
}

// English stage badges for rows that carry a service order.
const ORDER_STAGE_LABELS: Record<string, string> = {
  estimate: 'Quote pending',
  accepted: 'Quote accepted',
  paid: 'Paid, starting soon',
  processing: 'Service in progress',
  waiting_customer: 'Awaiting your input',
  delivered: 'Delivered, awaiting review',
  completed: 'Completed',
}

// English badge labels for matter-only rows, keyed by their tab category.
const CATEGORY_LABELS: Record<MatterCategory, string> = {
  conversation: 'In conversation',
  organizing: 'Organizing',
  connecting: 'Connecting',
  completed: 'Completed',
}

// Round 16 category rules. Orders win: any order that is not confirmed
// completed (invoice received) is still Connecting; only stage completed
// lands in Completed. A link with no resolvable order is Connecting too.
function orderCategory(stage?: string): MatterCategory {
  return stage === 'completed' ? 'completed' : 'connecting'
}

function orderLabel(stage?: string): string {
  return (stage && ORDER_STAGE_LABELS[stage]) || 'Status pending'
}

// Matter-only rows are categorized by the first blueprint step that is not
// completed (01 In Conversation; 02/03 Organizing; 04/05 Connecting). An
// empty blueprint is In Conversation; a fully completed blueprint counts as
// step 05 (Connecting). A completed matter without an order is Completed.
function blueprintCategory(matter: PersonalAgentMatter): MatterCategory {
  if (matter.status === 'completed') return 'completed'
  const steps = Array.isArray(matter.blueprint) ? matter.blueprint : []
  if (!steps.length) return 'conversation'
  const current = steps.find(step => step.status !== 'completed')
  const stageId = current ? current.id : 5
  if (stageId <= 1) return 'conversation'
  if (stageId <= 3) return 'organizing'
  return 'connecting'
}

function rowGroup(category: MatterCategory): 'active' | 'completed' {
  return category === 'completed' ? 'completed' : 'active'
}

// Presentation only: no local status may complete a canonical service order.
export function buildButlerMatterRows(matters: PersonalAgentMatter[], orders: OrderSummary[]): ButlerMatterRow[] {
  const orderMap = new Map(orders.map(order => [order.id, order]))
  const representedOrders = new Set<string>()
  const rows: ButlerMatterRow[] = matters.map(matter => {
    const rawOrderId = matter.knownFacts?.service_order_id
    const linkedOrderId = typeof rawOrderId === 'string' && rawOrderId.trim() ? rawOrderId.trim() : undefined
    const order = linkedOrderId ? orderMap.get(linkedOrderId) : undefined
    if (order) representedOrders.add(order.id)
    let category: MatterCategory
    let status: string
    if (order) {
      category = orderCategory(order.stage)
      status = orderLabel(order.stage)
    } else if (linkedOrderId) {
      category = 'connecting'
      status = 'Order sync pending'
    } else {
      category = blueprintCategory(matter)
      status = CATEGORY_LABELS[category]
    }
    return {
      id: matter.id, title: matter.title, matter, order, linkedOrderId,
      group: rowGroup(category), category,
      status,
      updatedAt: order?.updatedAt || matter.updatedAt,
    }
  })
  for (const order of orders) {
    if (representedOrders.has(order.id)) continue
    const category = orderCategory(order.stage)
    rows.push({
      id: `order:${order.id}`, title: order.serviceTitle || 'Professional service matter',
      matter: undefined, order, linkedOrderId: order.id,
      group: rowGroup(category), category,
      status: orderLabel(order.stage), updatedAt: order.updatedAt || '',
    })
  }
  return rows.sort((a, b) => (Date.parse(b.updatedAt) || 0) - (Date.parse(a.updatedAt) || 0))
}
