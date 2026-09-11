import { PersonalAgentMatter } from './personal-agent-matter'

export type ButlerActionPlanItem = {
  id: string
  title: string
  owner: 'butler' | 'owner' | 'professional'
  status: 'ready' | 'waiting' | 'blocked'
}

function strings(value: unknown) {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && Boolean(item.trim())) : []
}

export function buildButlerActionPlan(matter: PersonalAgentMatter): ButlerActionPlanItem[] {
  const agentActions = strings(matter.knownFacts.agent_can_do_next)
  const ownerActions = strings(matter.knownFacts.owner_actions)
  const missing = strings(matter.knownFacts.missing_information)
  const professionalNeeded = matter.knownFacts.professional_needed === true
  const category = typeof matter.knownFacts.professional_category === 'string' && matter.knownFacts.professional_category.trim() ? matter.knownFacts.professional_category.trim() : 'licensed professional'

  const items: ButlerActionPlanItem[] = []
  agentActions.forEach((title, index) => items.push({ id: `butler_${index}`, title, owner: 'butler', status: missing.length ? 'waiting' : 'ready' }))
  ownerActions.forEach((title, index) => items.push({ id: `owner_${index}`, title, owner: 'owner', status: 'waiting' }))
  missing.forEach((title, index) => items.push({ id: `missing_${index}`, title: `Provide or confirm: ${title}`, owner: 'owner', status: 'blocked' }))
  if (professionalNeeded) items.push({ id: 'professional_handoff', title: `Prepare a complete handoff package for the right ${category}.`, owner: 'professional', status: missing.length || ownerActions.length ? 'blocked' : 'ready' })
  if (!items.length) items.push({ id: 'butler_review', title: 'Review the Matter context and prepare the safest next action.', owner: 'butler', status: 'ready' })
  return items
}
