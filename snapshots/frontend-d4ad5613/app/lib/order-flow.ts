export type ServiceOrderStage =
  | 'estimate_draft'
  | 'estimate_sent'
  | 'estimate_accepted'
  | 'payment_pending'
  | 'paid'
  | 'processing'
  | 'waiting_customer'
  | 'delivered'
  | 'completed'
  | 'settlement_ready'
  | 'settled'

export type ServiceOrderMessageRole = 'customer' | 'agent' | 'customer_ai' | 'agent_ai' | 'system'

export type ServiceOrderMessage = {
  id: string
  role: ServiceOrderMessageRole
  text: string
  created_at: string
}

export type ServiceEstimate = {
  currency: 'USD'
  amount: number
  service_title: string
  scope: string
  sent_at?: string
  accepted_at?: string
}

export type ServiceOrderV1 = {
  id: string
  opportunity_id?: string
  stage: ServiceOrderStage
  estimate: ServiceEstimate
  customer_contact_hidden: true
  payment_status: 'unpaid' | 'paid' | 'refunded' | 'disputed'
  settlement_status: 'locked' | 'ready' | 'paid'
  agent_messages: ServiceOrderMessage[]
  customer_messages: ServiceOrderMessage[]
  created_at: string
  updated_at: string
}

export const SERVICE_ORDER_STAGE_LABELS: Record<ServiceOrderStage, string> = {
  estimate_draft: 'Preparing Quote',
  estimate_sent: 'Estimate Sent',
  estimate_accepted: 'Customer Accepted',
  payment_pending: 'Awaiting Payment',
  paid: 'Paid',
  processing: 'Service in Progress',
  waiting_customer: 'Waiting for Customer Info',
  delivered: 'Delivered',
  completed: 'Customer Confirmed',
  settlement_ready: 'Awaiting Settlement',
  settled: 'Settled',
}

export const SERVICE_ORDER_V1_RULES = {
  contactRelayOnly: true,
  goaaOrderCommissionPercent: 0,
  agentSubscriptionMonthlyUsd: 99,
  settlementRequiresCompletion: true,
  paymentProvider: 'stripe-connect',
} as const
