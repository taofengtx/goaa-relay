import { PersonalAgentMatter } from './personal-agent-matter'

export type ProfessionalHandoffPackage = {
  matterId: string
  title: string
  category: string | null
  summary: string | null
  organization: string | null
  dueDate: string | null
  amount: string | null
  urgency: string | null
  risks: string[]
  ownerActions: string[]
  agentNextSteps: string[]
  missingInformation: string[]
  boundary: string
}
function text(v:unknown){return typeof v==='string'&&v.trim()?v.trim():null}
function list(v:unknown){return Array.isArray(v)?v.filter((x):x is string=>typeof x==='string'&&Boolean(x.trim())).slice(0,8):[]}
export function buildProfessionalHandoffPackage(matter:PersonalAgentMatter):ProfessionalHandoffPackage{
 return {matterId:matter.id,title:matter.title,category:text(matter.knownFacts.professional_category),summary:text(matter.knownFacts.summary),organization:text(matter.knownFacts.organization),dueDate:text(matter.knownFacts.due_date),amount:matter.knownFacts.amount==null?null:String(matter.knownFacts.amount),urgency:text(matter.knownFacts.urgency),risks:list(matter.knownFacts.risk_flags),ownerActions:list(matter.knownFacts.owner_actions),agentNextSteps:list(matter.knownFacts.agent_can_do_next),missingInformation:list(matter.knownFacts.missing_information),boundary:'Customer AI Butler represents the customer. Professional AI Assistant represents the licensed professional. This package shares reviewed Matter context only; it does not authorize external action, payment, filing, advice, or completion.'}
}
