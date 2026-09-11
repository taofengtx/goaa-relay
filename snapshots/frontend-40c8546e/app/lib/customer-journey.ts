export type CustomerJourneyStep =
  | 'planning'
  | 'need_ready'
  | 'auth_required'
  | 'order_created'
  | 'connect_checkout_started'
  | 'connect_payment_verifying'
  | 'connect_paid'
  | 'matching'
  | 'matched'
  | 'order_workspace'

export type CustomerJourneyState = {
  orderId?: string
  step: CustomerJourneyStep
  planningSessionId?: string
  updatedAt: string
}

export const CUSTOMER_JOURNEY_KEYS = {
  workspace: 'goaa_planning_workspace_v1',
  orderId: 'goaa_active_order_id',
  journey: 'goaa_customer_e2e_journey_v1',
  clientToken: 'client_token',
  pendingPurchase: 'goaa_pending_purchase_v1',
  authReturn: 'goaa_auth_return_v1',
} as const

export function readCustomerJourney(): CustomerJourneyState | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(CUSTOMER_JOURNEY_KEYS.journey)
    return raw ? JSON.parse(raw) as CustomerJourneyState : null
  } catch {
    return null
  }
}

export function writeCustomerJourney(patch: Partial<CustomerJourneyState> & { step: CustomerJourneyStep }) {
  if (typeof window === 'undefined') return
  const current = readCustomerJourney()
  const next: CustomerJourneyState = {
    ...current,
    ...patch,
    step: patch.step,
    updatedAt: new Date().toISOString(),
  }
  window.localStorage.setItem(CUSTOMER_JOURNEY_KEYS.journey, JSON.stringify(next))
  if (next.orderId) window.localStorage.setItem(CUSTOMER_JOURNEY_KEYS.orderId, next.orderId)
}

export function customerToken() {
  if (typeof window === 'undefined') return ''
  return window.localStorage.getItem(CUSTOMER_JOURNEY_KEYS.clientToken) || ''
}

export function customerOrderId() {
  if (typeof window === 'undefined') return ''
  return readCustomerJourney()?.orderId || window.localStorage.getItem(CUSTOMER_JOURNEY_KEYS.orderId) || ''
}

export function prepareCustomerAuthReturn(target = '/connect-pass?source=planning') {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(CUSTOMER_JOURNEY_KEYS.pendingPurchase, target)
  window.localStorage.setItem(CUSTOMER_JOURNEY_KEYS.authReturn, target)
  writeCustomerJourney({ step: 'auth_required' })
}
