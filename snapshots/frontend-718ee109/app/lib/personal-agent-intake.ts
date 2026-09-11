const GOAA_API_URL = process.env.NEXT_PUBLIC_OPENCLAW_URL ?? 'https://api.goaa.ai'

export type IntakeSource = 'email_screenshot' | 'physical_mail' | 'document'
export type IntakeUrgency = 'low' | 'normal' | 'high' | 'urgent'

export type IntakeAnalysisSignal = {
  source: IntakeSource
  title: string
  summary: string
  organization: string | null
  document_type: string | null
  received_date: string | null
  due_date: string | null
  amount: string | null
  needs_action: boolean
  urgency: IntakeUrgency
  risk_flags: string[]
  owner_actions: string[]
  agent_can_do_next: string[]
  missing_information: string[]
  suggested_matter_title: string | null
  professional_needed: boolean
  professional_category: string | null
}

export type IntakeAnalysisResponse = {
  status: 'success'
  signal: IntakeAnalysisSignal
}

export async function analyzeAgentIntake(input: {
  file: File
  source: IntakeSource
  note?: string
}): Promise<IntakeAnalysisResponse> {
  const body = new FormData()
  body.append('file', input.file)
  body.append('source', input.source)
  if (input.note?.trim()) body.append('note', input.note.trim())

  const response = await fetch(`${GOAA_API_URL}/api/v1/agent/intake/analyze`, {
    method: 'POST',
    body,
  })

  if (!response.ok) {
    const message = await response.text().catch(() => '')
    throw new Error(`Document understanding failed: ${response.status}${message ? ` ${message.slice(0, 160)}` : ''}`)
  }

  const data = (await response.json()) as Partial<IntakeAnalysisResponse> & { message?: string }
  if (data.status !== 'success' || !data.signal) {
    throw new Error(data.message || 'The Agent could not understand this item yet.')
  }

  return data as IntakeAnalysisResponse
}
