export type KnowledgeVerificationStatus = 'recognized' | 'confirmed' | 'updated' | 'removed'

export type KnowledgeVerificationRecord = {
  signature: string
  status: KnowledgeVerificationStatus
  overrideValue?: string
  updatedAt: string
}

export const KNOWLEDGE_VERIFICATION_KEY = 'goaa_personal_agent_knowledge_verification_v1'
export const KNOWLEDGE_VERIFICATION_EVENT = 'goaa:knowledge-verification-changed'

export function knowledgeFactSignature(key: string, value: unknown) {
  let serialized = ''
  try { serialized = JSON.stringify(value) } catch { serialized = String(value) }
  return `${key}::${serialized}`
}

export function readKnowledgeVerification(): Record<string, KnowledgeVerificationRecord> {
  if (typeof window === 'undefined') return {}
  try {
    const raw = window.localStorage.getItem(KNOWLEDGE_VERIFICATION_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as Record<string, KnowledgeVerificationRecord>
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

export function saveKnowledgeVerification(record: KnowledgeVerificationRecord) {
  if (typeof window === 'undefined') return
  const all = readKnowledgeVerification()
  all[record.signature] = record
  window.localStorage.setItem(KNOWLEDGE_VERIFICATION_KEY, JSON.stringify(all))
  window.dispatchEvent(new CustomEvent(KNOWLEDGE_VERIFICATION_EVENT, { detail: { signature: record.signature } }))
}

export function setKnowledgeFactStatus(signature: string, status: KnowledgeVerificationStatus, overrideValue?: string) {
  saveKnowledgeVerification({
    signature,
    status,
    ...(status === 'updated' && overrideValue !== undefined ? { overrideValue } : {}),
    updatedAt: new Date().toISOString(),
  })
}
