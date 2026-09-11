import { AgentKnowledgeFact, derivePersonalKnowledge } from './personal-agent-knowledge'
import { readMatterHistory } from './personal-agent-matter'
import { knowledgeFactSignature, readKnowledgeVerification } from './personal-agent-knowledge-verification'

export type TrustedKnowledgeFact = {
  key: string
  value: unknown
  trust: 'owner_confirmed' | 'owner_updated'
  source: AgentKnowledgeFact
  verifiedAt: string
}

export function readTrustedOwnerKnowledge(): TrustedKnowledgeFact[] {
  if (typeof window === 'undefined') return []
  const recognized = derivePersonalKnowledge(readMatterHistory())
  const verification = readKnowledgeVerification()
  const trusted: TrustedKnowledgeFact[] = []

  for (const fact of recognized) {
    const signature = knowledgeFactSignature(fact.key, fact.value)
    const record = verification[signature]
    if (!record || record.status === 'recognized' || record.status === 'removed') continue

    trusted.push({
      key: fact.key,
      value: record.status === 'updated' ? record.overrideValue ?? fact.value : fact.value,
      trust: record.status === 'updated' ? 'owner_updated' : 'owner_confirmed',
      source: fact,
      verifiedAt: record.updatedAt,
    })
  }

  return trusted.sort((a, b) => Date.parse(b.verifiedAt) - Date.parse(a.verifiedAt))
}

export function trustedOwnerKnowledgeRecord(): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  for (const fact of readTrustedOwnerKnowledge()) result[fact.key] = fact.value
  return result
}
