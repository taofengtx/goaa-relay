export type AgentSignalSource = 'email_screenshot' | 'physical_mail' | 'document' | 'manual'
export type AgentSignalStatus = 'new' | 'understood' | 'needs_action' | 'resolved'
export type AgentSignalUrgency = 'low' | 'normal' | 'high' | 'urgent'

export type AgentSignal = {
  id: string
  source: AgentSignalSource
  title: string
  summary: string
  receivedAt: string
  status: AgentSignalStatus
  suggestedMatterTitle?: string
  dueDate?: string
  organization?: string
  amount?: string
  attachmentName?: string
  attachmentType?: string
  intakeNote?: string
  documentType?: string
  urgency?: AgentSignalUrgency
  riskFlags?: string[]
  ownerActions?: string[]
  agentCanDoNext?: string[]
  missingInformation?: string[]
  professionalNeeded?: boolean
  professionalCategory?: string
  analyzedAt?: string
  analysisError?: string
  ownerReviewedAt?: string
  linkedMatterId?: string
}

export const AGENT_SIGNAL_INBOX_KEY = 'goaa_personal_agent_signal_inbox_v1'
export const AGENT_SIGNAL_EVENT = 'goaa:agent-signal-changed'

export function readAgentSignals(): AgentSignal[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(AGENT_SIGNAL_INBOX_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as AgentSignal[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveAgentSignal(signal: AgentSignal) {
  if (typeof window === 'undefined') return
  const current = readAgentSignals()
  const next = [signal, ...current.filter((item) => item.id !== signal.id)].slice(0, 100)
  window.localStorage.setItem(AGENT_SIGNAL_INBOX_KEY, JSON.stringify(next))
  window.dispatchEvent(new CustomEvent(AGENT_SIGNAL_EVENT, { detail: { signalId: signal.id } }))
}

export function updateAgentSignal(signalId: string, patch: Partial<AgentSignal>) {
  const current = readAgentSignals()
  const existing = current.find((item) => item.id === signalId)
  if (!existing) return null
  const next = { ...existing, ...patch }
  saveAgentSignal(next)
  return next
}

export function createAttachmentSignal(input: {
  source: 'email_screenshot' | 'physical_mail' | 'document'
  fileName: string
  fileType?: string
  note?: string
}) {
  const now = new Date().toISOString()
  const kind = input.source === 'email_screenshot' ? 'Email screenshot' : input.source === 'physical_mail' ? 'Letter / Mail' : 'Document'
  const signal: AgentSignal = {
    id: `signal_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    source: input.source,
    title: `${kind}: ${input.fileName}`,
    summary: 'Waiting for AI understanding. The attachment has been captured as a new signal but has not been analyzed yet.',
    receivedAt: now,
    status: 'new',
    attachmentName: input.fileName,
    attachmentType: input.fileType,
    intakeNote: input.note?.trim() || undefined,
  }
  saveAgentSignal(signal)
  return signal
}
