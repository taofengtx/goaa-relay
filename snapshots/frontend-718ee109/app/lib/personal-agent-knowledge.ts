import { PersonalAgentMatter } from './personal-agent-matter'

export type AgentKnowledgeFact = {
  key: string
  value: unknown
  sourceMatterIds: string[]
  sourceMatterTitles: string[]
  sourceCount: number
  firstSeenAt: string
  lastSeenAt: string
}

function isUsableValue(value: unknown) {
  if (value === undefined || value === null) return false
  if (typeof value === 'string') return value.trim().length > 0
  if (Array.isArray(value)) return value.length > 0
  return true
}

function valueSignature(value: unknown) {
  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

export function derivePersonalKnowledge(matters: PersonalAgentMatter[]): AgentKnowledgeFact[] {
  const grouped = new Map<string, AgentKnowledgeFact>()

  for (const matter of matters) {
    for (const [key, value] of Object.entries(matter.knownFacts || {})) {
      if (!isUsableValue(value)) continue
      const signature = `${key}::${valueSignature(value)}`
      const existing = grouped.get(signature)

      if (!existing) {
        grouped.set(signature, {
          key,
          value,
          sourceMatterIds: [matter.id],
          sourceMatterTitles: [matter.title],
          sourceCount: 1,
          firstSeenAt: matter.createdAt,
          lastSeenAt: matter.updatedAt,
        })
        continue
      }

      if (!existing.sourceMatterIds.includes(matter.id)) {
        existing.sourceMatterIds.push(matter.id)
        existing.sourceMatterTitles.push(matter.title)
        existing.sourceCount += 1
      }
      if (Date.parse(matter.createdAt) < Date.parse(existing.firstSeenAt)) existing.firstSeenAt = matter.createdAt
      if (Date.parse(matter.updatedAt) > Date.parse(existing.lastSeenAt)) existing.lastSeenAt = matter.updatedAt
    }
  }

  return Array.from(grouped.values()).sort((a, b) => {
    if (b.sourceCount !== a.sourceCount) return b.sourceCount - a.sourceCount
    return Date.parse(b.lastSeenAt) - Date.parse(a.lastSeenAt)
  })
}
