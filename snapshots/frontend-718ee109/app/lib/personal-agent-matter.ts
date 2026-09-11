export type MatterStatus = 'active' | 'professional_handoff' | 'completed'

export type MatterThreadItem = { role: 'user' | 'assistant'; content: string; stage?: string }
export type MatterPlanStep = { id: number; title: string; status: 'active' | 'completed' | 'pending' | 'blocked' }

export type PersonalAgentMatter = {
  schemaVersion: 1
  number?: number
  id: string
  title: string
  status: MatterStatus
  source: 'planning_workspace' | 'agent_signal'
  createdAt: string
  updatedAt: string
  sessionId: string
  intent: string | null
  subIntent: string | null
  stage: string
  knownFacts: Record<string, unknown>
  thread: MatterThreadItem[]
  blueprint: MatterPlanStep[]
}

export type LegacyPlanningWorkspace = {
  thread?: MatterThreadItem[]
  sessionId?: string
  plan?: { steps?: MatterPlanStep[] } | null
  stage?: string
  intent?: string | null
  knownFacts?: Record<string, unknown>
  displayTitle?: string
  subIntent?: string | null
}

export const LEGACY_WORKSPACE_KEY = 'goaa_planning_workspace_v1'
export const CURRENT_MATTER_KEY = 'goaa_personal_agent_current_matter_v1'
export const MATTER_HISTORY_KEY = 'goaa_personal_agent_matter_history_v1'
export const MATTER_DEDUPE_KEY = 'goaa_personal_agent_matter_dedupe_v1'
export const MATTER_RESTORE_EVENT = 'goaa:matter-restored'

function stableMatterId(workspace: LegacyPlanningWorkspace) {
  const session = workspace.sessionId?.trim()
  if (session) return `matter_${session}`
  const firstUser = workspace.thread?.find((item) => item.role === 'user')?.content || 'current'
  let hash = 0
  for (let i = 0; i < firstUser.length; i += 1) hash = ((hash << 5) - hash + firstUser.charCodeAt(i)) | 0
  return `matter_local_${Math.abs(hash)}`
}

function deriveStatus(stage?: string): MatterStatus {
  if (stage === 'execute') return 'professional_handoff'
  if (stage === 'completed') return 'completed'
  return 'active'
}

export function matterFromLegacyWorkspace(workspace: LegacyPlanningWorkspace, previous?: PersonalAgentMatter | null): PersonalAgentMatter | null {
  const thread = Array.isArray(workspace.thread) ? workspace.thread : []
  if (!thread.length) return null
  const now = new Date().toISOString()
  const firstUser = thread.find((item) => item.role === 'user')?.content || 'Current Matter'
  const title = workspace.displayTitle && workspace.displayTitle !== 'GOAA Plan' ? workspace.displayTitle : firstUser.length > 56 ? `${firstUser.slice(0, 53)}…` : firstUser
  const id = stableMatterId(workspace)
  const previousSameMatter = previous?.id === id ? previous : null
  return { schemaVersion: 1, number: previousSameMatter?.number, id, title, status: deriveStatus(workspace.stage), source: 'planning_workspace', createdAt: previousSameMatter?.createdAt || now, updatedAt: now, sessionId: workspace.sessionId || '', intent: workspace.intent || null, subIntent: workspace.subIntent || null, stage: workspace.stage || '', knownFacts: workspace.knownFacts || {}, thread, blueprint: workspace.plan?.steps || [] }
}

export function readCurrentMatter(): PersonalAgentMatter | null {
  if (typeof window === 'undefined') return null
  try { const raw = window.localStorage.getItem(CURRENT_MATTER_KEY); if (!raw) return null; const parsed = JSON.parse(raw) as PersonalAgentMatter; return parsed?.schemaVersion === 1 ? parsed : null } catch { return null }
}

function readMatterHistoryRaw(): PersonalAgentMatter[] {
  if (typeof window === 'undefined') return []
  try { const raw = window.localStorage.getItem(MATTER_HISTORY_KEY); if (!raw) return []; const parsed = JSON.parse(raw) as PersonalAgentMatter[]; return Array.isArray(parsed) ? parsed.filter((item) => item?.schemaVersion === 1) : [] } catch { return [] }
}

function sameFirstUserContent(matter: PersonalAgentMatter | null | undefined, workspace: LegacyPlanningWorkspace): boolean {
  if (!matter) return false
  const left = matter.thread.find((item) => item.role === 'user')?.content
  const right = Array.isArray(workspace.thread) ? workspace.thread.find((item) => item.role === 'user')?.content : undefined
  return Boolean(left) && left === right
}

// Round 15 one-time cleanup of duplicate rows written before the
// "no matter before session; local row upgrades to the session row" rule:
// a local row (matter_local_<firstUserHash>) is dropped when a session row
// with the same first-user content already exists; lone local rows stay.
// Runs once, marked by MATTER_DEDUPE_KEY.
export function dedupeMatterHistoryOnce(): PersonalAgentMatter[] {
  if (typeof window === 'undefined') return []
  if (window.localStorage.getItem(MATTER_DEDUPE_KEY) === '1') return readMatterHistoryRaw()
  try {
    const history = readMatterHistoryRaw()
    const localRows = history.filter((item) => item.id.startsWith('matter_local_'))
    if (localRows.length) {
      const remove = new Set<string>()
      for (const local of localRows) {
        const hasSessionRow = history.some((item) => item.id !== local.id && !item.id.startsWith('matter_local_') && stableMatterId({ thread: item.thread, sessionId: '' }) === local.id)
        if (hasSessionRow) remove.add(local.id)
      }
      const cleaned = remove.size ? history.filter((item) => !remove.has(item.id)) : history
      window.localStorage.setItem(MATTER_HISTORY_KEY, JSON.stringify(cleaned))
    }
    window.localStorage.setItem(MATTER_DEDUPE_KEY, '1')
    return readMatterHistoryRaw()
  } catch { return readMatterHistoryRaw() }
}

// Reads are idempotent: the first read after a legacy duplicate set performs
// the one-time cleanup above.
export function readMatterHistory(): PersonalAgentMatter[] {
  return dedupeMatterHistoryOnce()
}

// One-time backfill only: matters missing a number get the next numbers in
// createdAt order; matters that already carry a number are never renumbered.
export function ensureMatterNumbers(matters: PersonalAgentMatter[]): PersonalAgentMatter[] {
  if (typeof window === 'undefined') return matters
  const missing = matters.filter((item) => typeof item.number !== 'number')
  if (!missing.length) return matters
  const missingSorted = [...missing].sort((a, b) => Date.parse(a.createdAt) - Date.parse(b.createdAt) || a.id.localeCompare(b.id))
  let next = matters.reduce((max, item) => Math.max(max, typeof item.number === 'number' ? item.number : 0), 0)
  const byId = new Map(missingSorted.map((item) => { next += 1; return [item.id, { ...item, number: next }] }))
  const updated = matters.map((item) => byId.get(item.id) || item)
  window.localStorage.setItem(MATTER_HISTORY_KEY, JSON.stringify(updated))
  return updated
}

export function saveMatterToHistory(matter: PersonalAgentMatter, removeIds: string[] = []): PersonalAgentMatter[] {
  if (typeof window === 'undefined') return []
  const existing = ensureMatterNumbers(readMatterHistory())
  const sameId = existing.find((item) => item.id === matter.id)
  // A number is minted only for genuinely new matters. Updates and
  // local->session upgrades carry the existing number (Round 15).
  const baseNumber = typeof matter.number === 'number' ? matter.number : sameId?.number
  const kept = existing.filter((item) => item.id !== matter.id && !removeIds.includes(item.id))
  const maxNumber = kept.reduce((max, item) => Math.max(max, typeof item.number === 'number' ? item.number : 0), 0)
  const stored = { ...matter, number: baseNumber ?? maxNumber + 1 }
  const next = [stored, ...kept].sort((a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt)).slice(0, 50)
  window.localStorage.setItem(MATTER_HISTORY_KEY, JSON.stringify(next))
  return next
}

export function workspaceFromMatter(matter: PersonalAgentMatter): LegacyPlanningWorkspace {
  return { thread: matter.thread, sessionId: matter.sessionId, plan: { steps: matter.blueprint }, stage: matter.stage, intent: matter.intent, knownFacts: matter.knownFacts, displayTitle: matter.title, subIntent: matter.subIntent }
}

export function restoreMatter(matterId: string): PersonalAgentMatter | null {
  if (typeof window === 'undefined') return null
  const target = readMatterHistory().find((item) => item.id === matterId)
  if (!target) return null
  const current = syncLegacyWorkspaceToCurrentMatter()
  if (current) saveMatterToHistory(current)
  window.localStorage.setItem(LEGACY_WORKSPACE_KEY, JSON.stringify(workspaceFromMatter(target)))
  window.localStorage.setItem(CURRENT_MATTER_KEY, JSON.stringify(target))
  window.dispatchEvent(new CustomEvent(MATTER_RESTORE_EVENT, { detail: { matterId: target.id } }))
  return target
}

// Shared persistence for both write paths (Round 15):
//   - allowLocalCreate=false (bridge auto-sync): a conversation with no
//     session id is never archived into a new matter, but an existing
//     current matter of the same conversation may still be updated.
//   - allowLocalCreate=true  (+ New archive): a sessionless chat may be
//     archived as a local matter (guests), and the same upgrade rules apply.
// When a session id first appears, an existing matter_local_<firstUserHash>
// row is upgraded to matter_<sessionId>, keeping number + createdAt and
// removing the old local row. Number is minted only for genuinely new rows.
function persistWorkspaceMatter(workspace: LegacyPlanningWorkspace, allowLocalCreate: boolean): PersonalAgentMatter | null {
  if (typeof window === 'undefined') return null
  try {
    const thread = Array.isArray(workspace.thread) ? workspace.thread : []
    if (!thread.some((item) => item.role === 'user')) return null
    const sessionId = (workspace.sessionId || '').trim()
    const history = readMatterHistory()
    const sessionMatterId = sessionId ? `matter_${sessionId}` : ''
    const localId = stableMatterId({ thread, sessionId: '' })
    const previous = readCurrentMatter()
    let seed: PersonalAgentMatter | null = null
    const removeIds: string[] = []
    if (sessionId) {
      seed = history.find((item) => item.id === sessionMatterId) || null
      if (!seed) {
        const local = history.find((item) => item.id === localId) || null
        if (local) { seed = local; removeIds.push(local.id) }
      }
    } else if (previous && sameFirstUserContent(previous, workspace)) {
      seed = previous
    } else if (!allowLocalCreate) {
      return null
    }
    const candidate = matterFromLegacyWorkspace(workspace, null)
    if (!candidate) return null
    if (seed) { candidate.number = seed.number; candidate.createdAt = seed.createdAt }
    return saveMatterToHistory(candidate, removeIds).find((item) => item.id === candidate.id) || candidate
  } catch { return null }
}

export function syncLegacyWorkspaceToCurrentMatter(): PersonalAgentMatter | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(LEGACY_WORKSPACE_KEY)
    if (!raw) return null
    const workspace = JSON.parse(raw) as LegacyPlanningWorkspace
    const stored = persistWorkspaceMatter(workspace, false)
    if (!stored) return null
    window.localStorage.setItem(CURRENT_MATTER_KEY, JSON.stringify(stored))
    return stored
  } catch { return null }
}

// + New: archive the current conversation as a numbered matter, then clear
// the current-matter pointer immediately (do not wait for the runtime bridge).
// Returns null when the workspace has no user message (nothing to archive).
export function archiveCurrentWorkspace(): PersonalAgentMatter | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(LEGACY_WORKSPACE_KEY)
    if (!raw) return null
    const workspace = JSON.parse(raw) as LegacyPlanningWorkspace
    const stored = persistWorkspaceMatter(workspace, true)
    if (!stored) return null
    window.localStorage.removeItem(CURRENT_MATTER_KEY)
    return stored
  } catch { return null }
}
