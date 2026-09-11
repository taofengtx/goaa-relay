'use client'

import { FormEvent, useEffect, useMemo, useState } from 'react'
import { chat, PlanData } from '../lib/openclaw'
import ProfessionalHandoffCard from './ProfessionalHandoffCard'
import ButlerMattersView from './ButlerMattersView'
import ButlerWelcome from './ButlerWelcome'
import PersonalAgentInbox from './PersonalAgentInbox'
import PersonalAgentKnowledge from './PersonalAgentKnowledge'
import AgentProblemSolvingModel from './AgentProblemSolvingModel'
import AgentMattersOverview from './AgentMattersOverview'
import LoginMenu from './LoginMenu'
import { decideGoldenSignOut } from '../lib/golden-signout'
import { LEGACY_WORKSPACE_KEY, MATTER_RESTORE_EVENT, archiveCurrentWorkspace } from '../lib/personal-agent-matter'
import { clearCustomerSession } from '../lib/customer-signout'

type ThreadItem = { role: 'user' | 'assistant'; content: string; stage?: string }
type ViewMode = 'conversation' | 'plan' | 'execution' | 'matters' | 'knowledge'
type LifeStage = { label: string; age: string; icon: string; description: string; prompt: string }
type SavedWorkspace = {
  thread: ThreadItem[]
  sessionId: string
  plan: PlanData | null
  stage: string
  intent: string | null
  knownFacts: Record<string, unknown>
  displayTitle: string
  subIntent: string | null
  selectedLifeStage: string
  handoffDismissed?: boolean
  dismissedFactCount?: number
  connectionReady?: boolean
}

const WORKSPACE_STORAGE_KEY = 'goaa_planning_workspace_v1'
const PENDING_PROMPT_KEY = 'goaa_pending_prompt_v1'
const AUTH_RETURN_KEY = 'goaa_auth_return_v1'
const AFTER_AUTH_ACTION_KEY = 'goaa_after_auth_action_v1'

// P4.4B conversation-driven handoff: trigger when enough structured
// information has been collected (domain-flexible — no hard-coded field
// list; any facts the engine extracts count toward readiness).
const HANDOFF_MIN_FACTS = 4
const HANDOFF_REOFFER_DELTA = 2
const CONNECT_PASS_TARGET = '/connect-pass?source=planning'

// P4.4B fallback structure extraction: some domains return empty knownFacts
// from the engine, so we heuristically mine structured signals from the
// user's own messages (still domain-flexible — just counts, not a schema).
const HINT_PATTERNS: { key: string; re: RegExp }[] = [
  { key: 'age', re: /(\d{1,2})\s*(?:岁|years?\s*old|yo\b)/i },
  { key: 'location', re: /在?([\u4e00-\u9fffA-Za-z]{2,12}(?:州|省|市|县|区|郡))|(?:in\s+|near\s+)([A-Z][a-zA-Z]{2,20})/ },
  { key: 'budget', re: /预算\s*([\d.]+)\s*万?美元?|预算.*?([\d.]+)\s*万|budget[^\d]*([\d.,]+)\s*k?/i },
  { key: 'family', re: /夫妻|结婚|家庭|孩子|子女|双收入|配偶|family|kids|spouse|married|children/i },
  { key: 'objective', re: /自住|学区|投资|出租|改善|置换|刚需|首套|school|education|retirement|protection|home|house|coverage|insurance/i },
  { key: 'financing', re: /贷款|按揭|首付|利率|mortgage|loan|down\s*payment|financing|credit/i },
  { key: 'timeline', re: /(\d+)\s*(?:年|个月)\s*内|一年内|尽快|一年以内|within\s+(\d+)|within\s+a\s+year|soon/i },
]

function extractClientHints(userTexts: string[]): Record<string, string> {
  const joined = userTexts.join(' ')
  const hints: Record<string, string> = {}
  for (const { key, re } of HINT_PATTERNS) {
    const match = joined.match(re)
    if (match) {
      const value = match[1] || match[2] || match[3] || match[0]
      if (value) hints[key] = value
    }
  }
  return hints
}

const suggestions = [
  { label: '买房', icon: '⌂', prompt: '我正在考虑买房，帮我梳理一下这一阶段需要准备什么。' },
  { label: '结婚成家', icon: '◇', prompt: '我准备结婚成家，帮我看看家庭预算、保障和责任变化需要怎么规划。' },
  { label: '生孩子', icon: '◌', prompt: '家里刚有孩子，帮我梳理保障、教育金和家庭现金流。' },
  { label: '教育规划', icon: '⌁', prompt: '我想提前准备孩子的大学教育金，帮我做一个规划。' },
  { label: '税务', icon: '%', prompt: '我有一个税务方面的问题，先帮我梳理需要准备哪些信息。' },
  { label: '移民', icon: '◎', prompt: '我有一个移民或跨境相关需求，帮我梳理身份、税务、保险和资产方面需要关注什么。' },
  { label: '退休', icon: '◔', prompt: '我想开始做退休规划，帮我拆解退休收入、医疗、税务和传承需要考虑的事项。' },
  { label: '创业', icon: '↗', prompt: '我准备创业，帮我整理现金流、商业风险、税务和保障需要怎么规划。' },
]

const lifeStages: LifeStage[] = [
  { label: 'Birth & Family', age: 'Family Foundation', icon: '◉', description: 'Protection · Identity · Foundations', prompt: '我想从出生与家庭建立阶段开始做整体规划。' },
  { label: 'School & Education', age: 'Growth Stage', icon: '⌁', description: 'Education Resources · Education Funds · Cash Flow', prompt: '我想从上学与教育阶段开始规划教育资源、教育资金和家庭现金流。' },
  { label: 'Graduation & Career', age: 'Career Start', icon: '↗', description: 'Income · Taxes · Benefits · Savings', prompt: '我刚进入毕业就业阶段，帮我梳理收入、税务、福利、保险和储蓄。' },
  { label: 'Marriage & Family', age: 'Family Formation', icon: '◇', description: 'Budget · Protection · Assets · Responsibilities', prompt: '我准备结婚成家，帮我梳理家庭预算、保障、资产与责任变化。' },
  { label: 'Parenting', age: 'Family Expansion', icon: '◌', description: 'Healthcare · Education Funds · Risk Management', prompt: '我进入生育育儿阶段，帮我梳理医疗、保障、教育金和家庭风险管理。' },
  { label: 'Home & Property', age: 'Asset Building', icon: '⌂', description: 'Budget · Mortgage · Insurance · Taxes', prompt: '我准备买房置业，帮我梳理预算、贷款、保险、税务和资产安排。' },
  { label: 'Entrepreneurship', age: 'Career Growth', icon: '△', description: 'Cash Flow · Business Risk · Taxes', prompt: '我进入创业或事业发展阶段，帮我梳理现金流、商业风险、税务和保障。' },
  { label: 'Immigration', age: 'Identity Change', icon: '◎', description: 'Identity · Taxes · Insurance · Assets', prompt: '我有移民或跨境安排，帮我梳理身份变化、税务、保险、资产与家庭安排。' },
  { label: 'Mid-Life Family', age: 'Peak Responsibility', icon: '◫', description: 'Protection · Education · Retirement · Elder Care', prompt: '我处于中年家庭责任高峰期，帮我一起看保障、教育、退休和父母照护。' },
  { label: 'Retirement', age: 'Retirement Stage', icon: '◔', description: 'Income · Healthcare · Taxes · Legacy', prompt: '我准备进入退休阶段，帮我梳理退休收入、医疗、税务、资产传承和长期照护。' },
]

const planItems = ['Clarify goals and priorities', 'Assess your situation and options', 'Build a personalized action plan', 'Connect with the right professional', 'Execute, track, and optimize']
const previewFlow = ['Understand where you are now', 'Fill key gaps with guided questions', 'Build your stage plan and next steps', 'Connect a licensed expert when execution is needed']

const PLAN_STATE_LABEL: Record<string, string> = { active: 'In Progress', completed: 'Completed', pending: 'Awaiting Update', blocked: 'Needs More Info' }
const PLAN_STATE_ICON: Record<string, string> = { active: '●', completed: '✓', pending: '○', blocked: '!' }
const STAGE_LABEL: Record<string, string> = { intake: 'Understanding Goals', clarify: 'Gathering Info', plan: 'Building Plan', execute: 'Professional Execution', connection_ready: 'Ready to Connect' }
const FACT_LABEL: Record<string, string> = {
  child_age: 'Child Age', monthly_budget: 'Monthly Budget', current_savings: 'Current Savings', college_start_age: 'College Start Age',
  college_type: 'School Type', location: 'Region', risk_preference: 'Risk Preference', target_amount: 'Target Amount',
  insured_person: 'Insured Person', coverage_goal: 'Coverage Goal', age: 'Age', benefit_type: 'Benefit Type',
  existing_coverage: 'Existing Coverage', coverage_amount: 'Coverage Amount', time_horizon: 'Time Horizon', health_status: 'Health Status',
}

const TOPIC_RULES = [
  { id: 'insurance', re: /保险|寿险|健康险|医疗险|重疾|保障/ },
  { id: 'tax', re: /税务|报税|退税|个税|所得税|W-?2|1099/i },
  { id: 'housing', re: /买房|房产|房贷|置业|mortgage/i },
  { id: 'education', re: /教育|大学|学费|教育金|college/i },
  { id: 'retirement', re: /退休|401\(?k\)?|IRA|养老金/i },
  { id: 'immigration', re: /移民|签证|身份|绿卡|庇护/ },
  { id: 'business', re: /创业|公司|企业|生意|business/i },
]

function hasClientSession() {
  return typeof window !== 'undefined' && Boolean(window.localStorage.getItem('client_token'))
}

function detectTopic(text: string) {
  return TOPIC_RULES.find((rule) => rule.re.test(text))?.id || null
}

export default function ChatComponent({ butlerMode = false }: { butlerMode?: boolean }) {
  const [message, setMessage] = useState('')
  const [thread, setThread] = useState<ThreadItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [sessionId, setSessionId] = useState('')
  const [plan, setPlan] = useState<PlanData | null>(null)
  const [stage, setStage] = useState('')
  const [intent, setIntent] = useState<string | null>(null)
  const [knownFacts, setKnownFacts] = useState<Record<string, unknown>>({})
  const [connectionReady, setConnectionReady] = useState(false)
  const [displayTitle, setDisplayTitle] = useState('GOAA Plan')
  const [subIntent, setSubIntent] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('conversation')
  const [selectedLifeStage, setSelectedLifeStage] = useState<string>('')
  const [hydrated, setHydrated] = useState(false)
  // Display only: keep SSR and the initial client render identical. Existing
  // authentication, login redirects and purchase guards remain unchanged.
  const [sessionVisible, setSessionVisible] = useState(false)
  // One-time banner after customer sign-out returns here via /planning?logged_out=1.
  const [signOutNotice, setSignOutNotice] = useState(false)
  useEffect(() => {
    const syncSessionDisplay = () => {
      try { setSessionVisible(hasClientSession()) }
      catch { setSessionVisible(false) }
    }
    const onStorage = (event: StorageEvent) => {
      if (event.key === 'client_token' || event.key === null) syncSessionDisplay()
    }
    syncSessionDisplay()
    window.addEventListener('storage', onStorage)
    window.addEventListener('focus', syncSessionDisplay)
    window.addEventListener('pageshow', syncSessionDisplay)
    return () => {
      window.removeEventListener('storage', onStorage)
      window.removeEventListener('focus', syncSessionDisplay)
      window.removeEventListener('pageshow', syncSessionDisplay)
    }
  }, [])
  // Consume /planning?logged_out=1 once: show the one-time sign-out banner,
  // then clean the query param so a refresh does not re-show it.
  useEffect(() => {
    if (typeof window === 'undefined') return
    const params = new URLSearchParams(window.location.search)
    if (params.get('logged_out') === '1') {
      setSignOutNotice(true)
      try { window.history.replaceState(window.history.state, '', window.location.pathname) } catch { /* non-fatal */ }
    }
  }, [])
  // Round C1.2: portal rails link to /planning?view=matters. Only butler mode
  // has a Matters view. The param is dropped after use (other params are kept)
  // so a refresh or a later Chat click is not pulled back to Matters.
  useEffect(() => {
    if (!butlerMode || typeof window === 'undefined') return
    const url = new URL(window.location.href)
    if (url.searchParams.get('view') !== 'matters') return
    setViewMode('matters')
    url.searchParams.delete('view')
    window.history.replaceState(window.history.state, '', `${url.pathname}${url.search}${url.hash}`)
  }, [butlerMode])
  // Agent-layer UI restore: reuse the existing Matter event and saved schema.
  // No submission, new session, matching or canonical action is triggered here.
  useEffect(() => {
    if (!butlerMode) return
    const restore = () => {
      if (loading) return
      try {
        const raw = window.localStorage.getItem(LEGACY_WORKSPACE_KEY)
        if (!raw) return
        const data = JSON.parse(raw) as SavedWorkspace
        if (!Array.isArray(data.thread)) return
        setThread(data.thread); setSessionId(data.sessionId || ''); setPlan(data.plan || null)
        setStage(data.stage || ''); setIntent(data.intent || null); setKnownFacts(data.knownFacts || {})
        setConnectionReady(data.connectionReady === true || data.stage === 'connection_ready')
        setDisplayTitle(data.displayTitle || 'GOAA Plan'); setSubIntent(data.subIntent || null)
        setSelectedLifeStage(data.selectedLifeStage || ''); setHandoffDismissed(Boolean(data.handoffDismissed))
        setDismissedFactCount(data.dismissedFactCount || 0); setError(''); setMessage(''); setViewMode('conversation')
      } catch { /* Leave the current conversation intact if the saved matter is invalid. */ }
    }
    window.addEventListener(MATTER_RESTORE_EVENT, restore)
    return () => window.removeEventListener(MATTER_RESTORE_EVENT, restore)
  }, [butlerMode, loading])
  // P4.4B handoff state: offered once per sufficient context; re-offered
  // only when substantially more information arrives after a decline.
  const [handoffDismissed, setHandoffDismissed] = useState(false)
  const [dismissedFactCount, setDismissedFactCount] = useState(0)

  const inWorkspace = thread.length > 0
  const showWorkspace = butlerMode || inWorkspace
  const statusLabel = useMemo(() => loading ? 'Analyzing' : error ? 'Retry' : stage ? STAGE_LABEL[stage] || stage : 'Ready', [loading, error, stage])
  const latestAssistant = [...thread].reverse().find((item) => item.role === 'assistant')?.content || ''
  const firstGoal = thread.find((item) => item.role === 'user')?.content || 'Your current life plan'

  // P4.4B readiness: not message-count based; based on structured facts the
  // engine has extracted (knownFacts, domain-flexible) plus heuristic client
  // hints mined from the user's own messages. Both count toward readiness.
  const clientHints = useMemo<Record<string, string>>(() => extractClientHints(thread.filter((item) => item.role === 'user').map((item) => item.content)), [thread])
  const engineFactCount = useMemo(() => Object.values(knownFacts).filter((v) => v !== undefined && v !== null && String(v).trim() !== '').length, [knownFacts])
  const filledFactCount = engineFactCount + Object.keys(clientHints).length
  // An explicit server-confirmed request must not be blocked by the optional
  // four-fact recommendation threshold. This only reveals a confirmation card.
  const handoffReady = connectionReady || stage === 'connection_ready' || (intent != null && filledFactCount >= HANDOFF_MIN_FACTS)
  const showHandoffCard = handoffReady && !handoffDismissed && !loading
  const handoffFacts = useMemo(() => ({ ...clientHints, ...knownFacts }), [clientHints, knownFacts])

  // P4.4B conversation language: fixed product UI stays English-first, the
  // handoff message follows the user's conversation language (CJK vs latin).
  const conversationLang = useMemo<'zh' | 'en'>(() => {
    const userTexts = thread.filter((item) => item.role === 'user').map((item) => item.content).join(' ')
    const cjk = (userTexts.match(/[\u4e00-\u9fff]/g) || []).length
    const latin = (userTexts.match(/[a-zA-Z]/g) || []).length
    return cjk > 0 && cjk >= latin / 2 ? 'zh' : 'en'
  }, [thread])

  function saveWorkspaceNow() {
    if (typeof window === 'undefined' || thread.length === 0) return
    const snapshot: SavedWorkspace = { thread, sessionId, plan, stage, intent, knownFacts, displayTitle, subIntent, selectedLifeStage, handoffDismissed, dismissedFactCount, connectionReady }
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(snapshot))
  }

  function sendToLogin(reason: 'purchase' | 'leave' | 'new-topic', prompt?: string) {
    saveWorkspaceNow()
    if (prompt) window.localStorage.setItem(PENDING_PROMPT_KEY, prompt)
    window.localStorage.setItem(AUTH_RETURN_KEY, '/?resume=1')
    window.localStorage.setItem('goaa_auth_reason_v1', reason)
    window.location.assign(`/client-login?resume=1&reason=${encodeURIComponent(reason)}`)
  }

  // Customer sign-out: whitelist cleanup only (see ../lib/customer-signout).
  // The butler nickname is migrated to the guest key first, the planning draft
  // (goaa_planning_workspace_v1) and agent-role/other preferences stay. This
  // performs NO network request — no order/match/checkout/payment/delete call.
  const [signOutError, setSignOutError] = useState<string | null>(null)
  async function handleCustomerSignOut() {
    if (typeof window === 'undefined') return
    setSignOutError(null)
    // Golden session bridge (Clerk builds): revoke -> clear -> Clerk sign-out.
    // 'failed' must stay visible and must not clear local credentials.
    const outcome = await decideGoldenSignOut(window, '/planning?logged_out=1')
    if (outcome.status === 'failed') {
      setSignOutError(outcome.message)
      return
    }
    try {
      clearCustomerSession(window.localStorage, window.sessionStorage)
    } catch { /* never let a storage edge case block navigation */ }
    setSessionVisible(false)
    // Full reload guarantees no in-memory React state re-hydrates old token/order.
    window.location.replace('/planning?logged_out=1')
  }

  async function submitPrompt(prompt: string) {
    const clean = prompt.trim()
    if (!clean || loading) return

    if (typeof window !== 'undefined' && !hasClientSession() && thread.length >= 2) {
      const currentTopic = detectTopic(`${displayTitle} ${firstGoal}`)
      const nextTopic = detectTopic(clean)
      if (currentTopic && nextTopic && currentTopic !== nextTopic) {
        sendToLogin('new-topic', clean)
        return
      }
    }

    setThread((items) => [...items, { role: 'user', content: clean }])
    setLoading(true)
    setError('')
    setMessage('')
    setViewMode('conversation')

    try {
      const result = await chat('goaa_ai_product_entry', clean, sessionId || undefined)
      setSessionId(result.sessionId)
      setStage(result.stage)
      setIntent(result.intent)
      setKnownFacts(result.knownFacts)
      setConnectionReady(result.connectionReady || result.stage === 'connection_ready')
      if ((result.connectionReady || result.stage === 'connection_ready') && result.productAction !== 'fee_info') setHandoffDismissed(false)
      if (result.productAction === 'decline') {
        setHandoffDismissed(true)
        setDismissedFactCount(filledFactCount)
      }
      setDisplayTitle(result.displayTitle)
      setSubIntent(result.subIntent)
      setThread((items) => [...items, { role: 'assistant', content: result.response, stage: result.stage }])
      if (result.plan?.steps?.length) setPlan(result.plan)
    } catch (err: any) {
      setError(err?.message || 'GOAA is temporarily unavailable. Please try again later.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const saved = window.localStorage.getItem(WORKSPACE_STORAGE_KEY)
    if (saved) {
      try {
        const data = JSON.parse(saved) as SavedWorkspace
        setThread(Array.isArray(data.thread) ? data.thread : [])
        setSessionId(data.sessionId || '')
        setPlan(data.plan || null)
        setStage(data.stage || '')
        setIntent(data.intent || null)
        setKnownFacts(data.knownFacts || {})
        setConnectionReady(data.connectionReady === true || data.stage === 'connection_ready')
        setDisplayTitle(data.displayTitle || 'GOAA Plan')
        setSubIntent(data.subIntent || null)
        setSelectedLifeStage(data.selectedLifeStage || '')
        setHandoffDismissed(Boolean(data.handoffDismissed))
        setDismissedFactCount(data.dismissedFactCount || 0)
      } catch {
        window.localStorage.removeItem(WORKSPACE_STORAGE_KEY)
      }
    }

    setHydrated(true)
  }, [])

  useEffect(() => {
    if (!hydrated || thread.length === 0) return
    const snapshot: SavedWorkspace = { thread, sessionId, plan, stage, intent, knownFacts, displayTitle, subIntent, selectedLifeStage, handoffDismissed, dismissedFactCount, connectionReady }
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(snapshot))
  }, [hydrated, thread, sessionId, plan, stage, intent, knownFacts, displayTitle, subIntent, selectedLifeStage, handoffDismissed, dismissedFactCount, connectionReady])

  useEffect(() => {
    if (!hydrated || loading) return
    const pending = window.localStorage.getItem(PENDING_PROMPT_KEY)
    if (!pending) return
    window.localStorage.removeItem(PENDING_PROMPT_KEY)
    void submitPrompt(pending)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated])

  useEffect(() => {
    if (!hydrated || !inWorkspace || hasClientSession()) return
    if (!window.history.state?.goaaGuestGuard) {
      window.history.pushState({ ...(window.history.state || {}), goaaGuestGuard: true }, '', window.location.href)
    }
    const handlePopState = () => sendToLogin('leave')
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, inWorkspace])

  async function handleSend(event?: FormEvent) {
    event?.preventDefault()
    await submitPrompt(message)
  }

  function startLifeStage(item: LifeStage) {
    setSelectedLifeStage(item.label)
    void submitPrompt(item.prompt)
  }

  // P4.4B canonical handoff route: /connect-pass?source=planning.
  // No /api/stripe/* here — Order Engine remains canonical. Auth return is
  // preserved: anonymous customers continue the purchase journey after sign-in.
  function continueToProfessional() {
    saveWorkspaceNow()
    window.localStorage.setItem(AUTH_RETURN_KEY, CONNECT_PASS_TARGET)
    window.localStorage.setItem('goaa_auth_reason_v1', 'purchase')
    if (!hasClientSession()) {
      window.location.assign('/client-login?resume=1&reason=purchase')
      return
    }
    window.location.assign(CONNECT_PASS_TARGET)
  }

  // Butler + New: archive the current chat as a numbered matter (updates the
  // restored matter in place when it came from Matters), then start fresh.
  // No login redirect here — archiving works for guests via local matters.
  function handleNewMatter() {
    if (typeof window !== 'undefined') archiveCurrentWorkspace()
    if (typeof window !== 'undefined') window.localStorage.removeItem(WORKSPACE_STORAGE_KEY)
    setConnectionReady(false)
    setThread([]); setError(''); setLoading(false); setSessionId(''); setPlan(null); setStage(''); setIntent(null); setKnownFacts({}); setMessage(''); setViewMode('conversation'); setSelectedLifeStage(''); setDisplayTitle('GOAA Plan'); setSubIntent(null); setHandoffDismissed(false); setDismissedFactCount(0)
  }

  function resetHome() {
    if (typeof window !== 'undefined' && !hasClientSession() && thread.length > 0) {
      window.localStorage.setItem(AFTER_AUTH_ACTION_KEY, 'new_plan')
      sendToLogin('new-topic')
      return
    }
    if (typeof window !== 'undefined') window.localStorage.removeItem(WORKSPACE_STORAGE_KEY)
    setConnectionReady(false)
    setThread([]); setError(''); setLoading(false); setSessionId(''); setPlan(null); setStage(''); setIntent(null); setKnownFacts({}); setMessage(''); setViewMode('conversation'); setSelectedLifeStage(''); setDisplayTitle('GOAA Plan'); setSubIntent(null); setHandoffDismissed(false); setDismissedFactCount(0)
  }

  useEffect(() => {
    if (!hydrated || !hasClientSession()) return
    const action = window.localStorage.getItem(AFTER_AUTH_ACTION_KEY)
    if (action !== 'new_plan') return
    window.localStorage.removeItem(AFTER_AUTH_ACTION_KEY)
    window.localStorage.removeItem(WORKSPACE_STORAGE_KEY)
    setConnectionReady(false)
    setThread([]); setSessionId(''); setPlan(null); setStage(''); setIntent(null); setKnownFacts({}); setDisplayTitle('GOAA Plan'); setSubIntent(null); setSelectedLifeStage(''); setViewMode('conversation'); setHandoffDismissed(false); setDismissedFactCount(0)
  }, [hydrated])

  // P4.4B: notify the global ProfessionalConnectBar to hide while the user is
  // actively inside a consultation (top bar should not dominate/overlap).
  useEffect(() => {
    if (typeof window === 'undefined') return
    window.dispatchEvent(new CustomEvent('goaa:consultation-active', { detail: { active: inWorkspace } }))
  }, [inWorkspace])

  // P4.4B decline guard: after "Continue with AI", do NOT re-prompt on every
  // message; a later contextual re-offer is allowed only when substantially
  // more structured information arrives (facts delta >= HANDOFF_REOFFER_DELTA).
  useEffect(() => {
    if (handoffDismissed && filledFactCount >= dismissedFactCount + HANDOFF_REOFFER_DELTA) {
      setHandoffDismissed(false)
    }
  }, [filledFactCount, handoffDismissed, dismissedFactCount])

  const renderedPlan = plan?.steps?.length ? plan.steps : planItems.map((title, index) => ({ id: index + 1, title, status: index === 0 ? 'active' as const : 'pending' as const }))

  return (
    <div className={`goaa-shell${butlerMode ? ' butler-workspace' : ''}`}>
      <header className="goaa-nav">
        <a className="goaa-brand" href="https://goaa.ai/" aria-label="AI Butler home"><span className="goaa-mark">G</span><span className="goaa-brand-text">AI Butler</span></a>
        <nav className="goaa-nav-actions" aria-label="Primary navigation"><LoginMenu variant="ghost" signedIn={sessionVisible} onLogout={handleCustomerSignOut} error={signOutError} />{!showWorkspace && <a href="#start" className="goaa-start-link">Start Planning <span>→</span></a>}</nav>
      </header>
      {signOutNotice && (
        <div className="goaa-signout-notice" role="status">
          <span>已退出登录；此浏览器中的规划草稿仍保留。</span>
          <button type="button" aria-label="关闭提示" onClick={() => setSignOutNotice(false)}>×</button>
        </div>
      )}

      {!showWorkspace ? (
        <main className="goaa-entry" id="start">
          <section className="goaa-hero" aria-labelledby="goaa-title">
            <div className="goaa-hero-glow" aria-hidden="true" />
            <div className="hero-eyebrow">GOAA · AI LIFE PLANNING</div>
            <h1 id="goaa-title">Let AI plan your life,<br /><span>and licensed experts bring it to life.</span></h1>
            <p className="goaa-subtitle">Start with what&apos;s happening in your life right now — buying a home, getting married, having a child, changing jobs, starting a business, immigrating, insurance, taxes, retirement. AI helps you see what matters at this stage, and connects you with the right licensed expert when professional execution is needed.</p>

            <form className="goaa-composer" onSubmit={handleSend}>
              <div className="goaa-input-row"><span className="goaa-mic" aria-hidden="true">⌁</span><textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Tell GOAA: what's happening, what you're worried about, what you want to achieve…" rows={2} /><button type="submit" disabled={!message.trim() || loading}>↑</button></div>
            </form>

            <div className="goaa-suggestions" aria-label="Common life events">{suggestions.map((item) => <button key={item.label} type="button" onClick={() => void submitPrompt(item.prompt)}><span className="goaa-pill-icon">{item.icon}</span>{item.label}</button>)}</div>

            <section className="life-stage-section" aria-labelledby="life-stage-title">
              <div className="life-stage-heading"><div><span className="workspace-kicker">Life stage navigator</span><h2 id="life-stage-title">Start from a Life Stage</h2></div><span>You can also chat directly — both entries use the same planning engine</span></div>
              <div className="life-stage-timeline">
                <div className="life-stage-line" aria-hidden="true" />
                {lifeStages.map((item) => (
                  <button className={`life-stage-node ${selectedLifeStage === item.label ? 'selected' : ''}`} key={item.label} type="button" onClick={() => startLifeStage(item)}>
                    <span className="life-stage-dot">{item.icon}</span><span className="life-stage-age">{item.age}</span><strong>{item.label}</strong><small>{item.description}</small>
                  </button>
                ))}
              </div>
            </section>

            <div className="goaa-value-row">
              <div className="goaa-value-item"><span className="goaa-value-icon">◎</span><div><strong>Free AI Planning</strong><small>Identify your life stage; review your situation, risks, opportunities, and next steps.</small></div></div>
              <div className="goaa-value-item"><span className="goaa-value-icon">◌</span><div><strong>Guided First, Open-Ended Second</strong><small>Structure information as you chat; even detours keep the current planning task.</small></div></div>
              <div className="goaa-value-item"><span className="goaa-value-icon">◇</span><div><strong>Connect Experts Only When Needed</strong><small>Connect with a licensed professional only when the next step truly needs one — $39.90 one-time connection fee, 30-day access, no auto-renewal.</small></div></div>
            </div>

            <section className="goaa-plan-preview" aria-label="How GOAA works"><div className="goaa-plan-main"><div className="goaa-plan-heading"><span><b>✦</b> How GOAA Works</span><em>Planning is the main thread</em></div><div className="goaa-plan-list">{previewFlow.map((item, index) => <div className="goaa-plan-item" key={item}><span className="goaa-check">✓</span><span>{index + 1}. {item}</span><span className="goaa-chevron">›</span></div>)}</div></div><div className="goaa-orbit" aria-hidden="true"><span className="orbit orbit-one" /><span className="orbit orbit-two" /><span className="orbit orbit-three" /><span className="orbit-dot dot-a" /><span className="orbit-dot dot-b" /><span className="orbit-core">G</span></div></section>
          </section>
        </main>
      ) : (
        <main className={`workspace-shell${viewMode === 'matters' || viewMode === 'knowledge' ? ' butler-wide-view' : ''}`}>
          <aside className="workspace-rail">
            <button type="button" onClick={butlerMode ? handleNewMatter : resetHome} disabled={loading} className="workspace-new">{butlerMode ? '+ New' : '＋ New Plan'}</button>
            <div className="workspace-nav-label">{butlerMode ? 'MY AI BUTLER' : 'Planning workspace'}</div>
            <button className={`workspace-nav-item ${viewMode === 'conversation' ? 'active' : ''}`} onClick={() => setViewMode('conversation')}>Chat</button>
            {butlerMode && <button className={`workspace-nav-item ${viewMode === 'matters' ? 'active' : ''}`} onClick={() => setViewMode('matters')}>Matters</button>}
            {butlerMode && <a className="workspace-nav-item" href="/agent-loop/customer/skills">Skills Marketplace</a>}
            {butlerMode && <div className="workspace-rail-divider" />}
            {butlerMode && <a className="workspace-nav-item" href="/agent-loop/customer/get-licensed">Get Licensed <span className="workspace-nav-tag">NEW</span></a>}
            {butlerMode && <a className="workspace-nav-item" href="/agent-loop/customer/earning">Earning Paths <span className="workspace-nav-tag">NEW</span></a>}
            {!butlerMode && <button className={`workspace-nav-item ${viewMode === 'plan' ? 'active' : ''}`} onClick={() => setViewMode('plan')}>Plan Result</button>}
            {!butlerMode && <button className={`workspace-nav-item ${viewMode === 'execution' ? 'active' : ''}`} onClick={() => setViewMode('execution')}>Professional Execution</button>}
            <div className="workspace-rail-spacer" />
            {butlerMode && <button className={`workspace-nav-item ${viewMode === 'knowledge' ? 'active' : ''}`} onClick={() => setViewMode('knowledge')}>记忆与能力</button>}
            <small>{sessionVisible ? 'Signed in: GOAA auto-saves your plan and conversation — refresh or return anytime.' : 'Plan freely without signing in; sign in when purchasing, leaving, or switching topics to save.'}</small>
          </aside>

          <section className="workspace-conversation">
            {viewMode === 'conversation' && <>
              <div className="workspace-section-head"><div><span className="workspace-kicker">Current planning task</span><h2>{displayTitle && displayTitle !== 'GOAA Plan' ? displayTitle : 'New Matter'}</h2></div><span className="workspace-status">{statusLabel}</span></div>
              <div className="workspace-thread">
                {butlerMode && <ButlerWelcome />}
                {thread.map((item, index) => item.role === 'user' ? <div className="chat-row user" key={`${item.role}-${index}`}><span className="chat-avatar">You</span><div className="chat-bubble">{item.content}</div></div> : <div className="chat-row assistant" key={`${item.role}-${index}`}><span className="chat-avatar goaa">G</span><div className="chat-bubble assistant-bubble"><b>{item.stage ? STAGE_LABEL[item.stage] || item.stage : 'GOAA Plan Assistant'}</b><p>{item.content}</p></div></div>)}
                {loading && <div className="chat-row assistant"><span className="chat-avatar goaa">G</span><div className="chat-bubble assistant-bubble"><b>GOAA is analyzing your current stage…</b><p>Reviewing your task, known info, and gaps to decide whether to ask more or build your plan.</p></div></div>}
                {!loading && error && <div className="chat-row assistant"><span className="chat-avatar goaa">G</span><div className="chat-bubble assistant-bubble"><b>Connection Issue</b><p className="goaa-error">{error}</p></div></div>}
              </div>
              {showHandoffCard && (
                <div className="handoff-inline">
                  <ProfessionalHandoffCard
                    lang={conversationLang}
                    facts={handoffFacts}
                    onConnect={continueToProfessional}
                    onContinue={() => { setHandoffDismissed(true); setDismissedFactCount(filledFactCount) }}
                  />
                </div>
              )}
              {butlerMode && <details className="butler-inline-inbox"><summary>＋ 上传信件 / 照片 / PDF</summary><fieldset disabled={loading} className="butler-tool-fieldset"><PersonalAgentInbox /></fieldset></details>}
              <form className="workspace-composer" onSubmit={handleSend}><textarea aria-label="发给 AI 管家的消息" value={message} onChange={(e) => setMessage(e.target.value)} rows={2} placeholder={butlerMode ? '告诉我需要处理什么，或继续聊刚才的事…' : 'Continue with details, ask freely, or tell GOAA what’s next…'} /><button type="submit" aria-label="发送消息" disabled={!message.trim() || loading}>↑</button></form>
            </>}

            {butlerMode && viewMode === 'matters' && <ButlerMattersView busy={loading} onSignIn={() => sendToLogin('leave')} />}
            {butlerMode && viewMode === 'knowledge' && <section className="butler-capabilities" aria-label="管家的记忆与能力"><PersonalAgentKnowledge /><AgentProblemSolvingModel /><p className="butler-notice">已有的本机记忆与能力在此查看，不改变您的订单或授权。</p></section>}

            {viewMode === 'plan' && <section className="planning-result-view">
              <div className="result-hero"><span className="workspace-kicker">Life plan result</span><h2>Your Stage Plan</h2><p>{firstGoal}</p></div>
              <div className="result-grid">
                <article className="result-card"><span>01</span><h3>Current Status</h3><p>{Object.keys(knownFacts).length ? 'GOAA structured key information from our conversation into your profile.' : 'Keep chatting and GOAA will build your structured profile.'}</p><div className="fact-grid">{Object.entries(knownFacts).map(([key, value]) => <div key={key}><small>{FACT_LABEL[key] || key}</small><strong>{String(value)}</strong></div>)}</div></article>
                <article className="result-card"><span>02</span><h3>Current Assessment</h3><p>{latestAssistant || 'Once info is complete, GOAA generates risk, opportunity, and feasibility assessment.'}</p></article>
                <article className="result-card"><span>03</span><h3>Priorities & Action Plan</h3><div className="result-plan-list">{renderedPlan.map((step) => <div key={step.id} className={`result-plan-step ${step.status}`}><span>{PLAN_STATE_ICON[step.status] || '○'}</span><div><strong>{step.title}</strong><small>{PLAN_STATE_LABEL[step.status] || step.status}</small></div></div>)}</div></article>
              </div>
              <div className="result-note">Planning creates value first. We only connect you to a licensed professional when the next step truly needs a license, a quote, professional liability, or real execution.</div>
              {butlerMode && <details className="butler-existing-tools"><summary>查看已有事项评估与行动工具</summary><fieldset disabled={loading} className="butler-tool-fieldset"><AgentMattersOverview /></fieldset></details>}
            </section>}

            {viewMode === 'execution' && <section className="execution-view">
              <div className="execution-eyebrow">Professional execution</div>
              {showHandoffCard ? (
                <>
                  <h2>{stage === 'execute' ? 'Your Plan Has Entered Professional Execution' : 'Ready for Professional Handoff'}</h2>
                  <p>{stage === 'execute' ? 'This step requires a licensed expert matching your region, license, and specialty.' : 'GOAA now understands your needs well enough to introduce a licensed professional. Review the handoff summary below — you stay in control.'}</p>
                  <div className="execution-handoff">
                    <ProfessionalHandoffCard
                      lang={conversationLang}
                      facts={handoffFacts}
                      onConnect={continueToProfessional}
                      onContinue={() => { setHandoffDismissed(true); setDismissedFactCount(filledFactCount); setViewMode('conversation') }}
                    />
                  </div>
                  <div className="execution-offer">
                    <ul><li>Keep your AI-completed needs review and plan</li><li>Get a standardized professional request card</li><li>Match by region, license, and specialty</li><li>See expert status and service progress</li><li>Continue receiving AI-assisted summaries and reminders for 30 days</li><li>Re-match by rule if the first expert cannot take the case</li></ul>
                  </div>
                </>
              ) : (
                <>
                  <h2>Professional Execution Opens When Truly Needed</h2>
                  <p>Keep planning for free. GOAA never interrupts planning to charge — professional handoff opens in conversation only when a step truly needs a license, a quote, professional liability, or real execution.</p>
                  <div className="execution-offer">
                    <ul><li>GOAA keeps structuring your situation as you chat</li><li>When enough is understood, a handoff card appears right in the conversation</li><li>Connect only if you want to — otherwise continue planning with AI</li></ul>
                    <button className="execution-cta secondary" type="button" onClick={() => setViewMode('conversation')}>Continue Free Planning</button>
                  </div>
                </>
              )}
            </section>}
          </section>

          <aside className="workspace-plan">
            <div className="workspace-plan-head"><div><span className="workspace-kicker">Your Plan</span><h3>Action Blueprint</h3></div><span className="plan-badge">{stage ? STAGE_LABEL[stage] || stage : 'Live'}</span></div>
            <div className="workspace-plan-summary">Conversation is continuously structured into a plan — clarify when info is missing, generate when it&apos;s ready.</div>
            {Object.keys(knownFacts).length > 0 && <div className="known-facts-card"><span>Recognized Info</span>{Object.entries(knownFacts).slice(0, 6).map(([key, value]) => <div key={key}><small>{FACT_LABEL[key] || key}</small><strong>{String(value)}</strong></div>)}</div>}
            <div className="workspace-plan-list">{renderedPlan.map((step) => <button type="button" className={`workspace-plan-item ${step.status === 'active' ? 'current' : ''} ${step.status === 'completed' ? 'done' : ''}`} key={step.id} onClick={() => setViewMode('plan')}><span className="plan-index">0{step.id}</span><div><strong>{step.title}</strong><small>{PLAN_STATE_LABEL[step.status] || step.status}</small></div><span className="plan-state">{PLAN_STATE_ICON[step.status] || '○'}</span></button>)}</div>
            <button className={`professional-card ${stage === 'execute' || handoffReady ? 'ready' : ''}`} type="button" onClick={() => setViewMode('execution')}><span>◇</span><div><strong>{stage === 'execute' || handoffReady ? 'Professional Handoff Ready' : 'Professional Connection'}</strong><small>{stage === 'execute' || handoffReady ? 'Review the handoff card in conversation' : 'A licensed professional is introduced in conversation when your needs are clear — no pushy upsells.'}</small></div><b>›</b></button><a className="cal-card" href="https://cal.com/goaa.ai/30min" target="_blank" rel="noopener noreferrer"><span className="cal-card-mark">🗓</span><div className="cal-card-body"><strong>预约 30 分钟评估</strong><small>与 GOAA 团队进一步梳理目标和下一步。</small><span className="cal-card-cta">预约时间 ↗</span><em>预约不会自动购买 GOAA $39.90 专业人士连接服务，也不会触发平台扣款。</em></div></a>
          </aside>
        </main>
      )}

      <footer className="goaa-footer"><span>© 2026 GOAA.ai · AI plans, licensed experts execute</span><div><a href="https://www.goaa.ai/privacy" target="_blank" rel="noopener noreferrer">Privacy</a><a href="https://www.goaa.ai/terms" target="_blank" rel="noopener noreferrer">Terms</a><a href="/">Security</a></div></footer>
    </div>
  )
}
