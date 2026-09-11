const API_BASE = process.env.NEXT_PUBLIC_OPENCLAW_URL ?? "https://api.goaa.ai"

export type AgentProfile = {
  agent_id: string
  name: string
  email?: string
  license_type?: string
  license_number?: string
  states: string[]
  languages: string[]
  specialties: string[]
}

export type KnowledgeDocument = {
  id: string
  name: string
  type?: string
  size?: number
  status: "processing" | "ready" | "failed"
  chunks?: number
  uploaded_at?: string
}

export type AgentPreferences = {
  response_style: "concise" | "detailed" | "educational" | "consultative"
  priorities: string[]
  preferred_products: string[]
  preferred_carriers: string[]
  language_mode: "auto" | "zh" | "en"
  custom_instructions: string
}

export type AgentLead = {
  id: string
  category: string
  summary: string
  status: "available" | "accepted" | "declined" | "closed"
  created_at?: string
  client_region?: string
}

export type AgentSkill = {
  id: string
  name: string
  domain: string
  version?: string
  enabled: boolean
  knowledge_document_count: number
  knowledge_chunk_count: number
  coverage_status: "empty" | "partial" | "ready"
  missing_knowledge?: string[]
  last_indexed_at?: string
}

export type AgentAIPreviewRequest = {
  skill_id: string
  message: string
  known_facts?: Record<string, unknown>
}

export type AgentAIPreviewSource = {
  layer: "platform_skill" | "platform_knowledge" | "agent_private_knowledge" | "agent_preferences" | "general_model"
  label?: string
  document_id?: string
  filename?: string
  score?: number
  note?: string
}

export type AgentAIPreviewResponse = {
  response: string
  stage: "discovery" | "clarify" | "ready" | "connection_ready"
  connection_ready: boolean
  need_package?: Record<string, unknown>
  known_facts?: Record<string, unknown>
  missing_fields?: string[]
  sources: AgentAIPreviewSource[]
  applied_preferences?: Record<string, unknown> | string[]
}

// ════════════════════════════════════════════════════════════
// Payout account (Stripe Connect payout) — Golden Candidate Final UX
// - Account Link creation only happens on the Agent onboarding flow
// - readiness only comes from server-side verification
//   (POST /agents/me/connect-account/verify → transfers=active)
// - bearer token never goes into the URL; onboarding return only carries order_id +
//   onboarding flags and other non-sensitive navigation context
// ════════════════════════════════════════════════════════════
export type PayoutAccountState = {
  account_id: string
  account_type: string
  controller_type: string
  requirements_status: string
  currently_due: string[]
  disabled_reason: string
  transfers_capability: string
  onboarding_required: boolean
  ready: boolean
}

export type PayoutAccountView =
  | { status: "no_account"; state: PayoutAccountState }
  | { status: "ready"; state: PayoutAccountState }
  | { status: "incomplete"; state: PayoutAccountState }
  | { status: "restricted"; state: PayoutAccountState }

/** Server-side retrieve of the agent's Stripe Connect payout account. */
export async function getPayoutAccountState(): Promise<PayoutAccountState> {
  const raw = await request<{ state: PayoutAccountState; onboarding_complete: boolean }>(
    "/api/v1/order/agents/me/connect-account",
  )
  return raw.state
}

/** Start/continue Stripe hosted onboarding. Returns the hosted Account Link URL. */
export async function createPayoutAccountLink(orderId = ""): Promise<{ url: string; expires_at: string }> {
  const q = orderId ? `?order_id=${encodeURIComponent(orderId)}` : ""
  return request<{ url: string; expires_at: string }>(
    `/api/v1/order/agents/me/connect-account/link${q}`,
    { method: "POST" },
  )
}

/** Server-side verification after onboarding return. ready only if transfers=active. */
export async function verifyPayoutAccount(): Promise<{ ready: boolean; state: PayoutAccountState }> {
  return request<{ ready: boolean; state: PayoutAccountState }>(
    "/api/v1/order/agents/me/connect-account/verify",
    { method: "POST" },
  )
}

/** Map raw Stripe/GOAA state into the four UI states shown in Agent Console. */
export function payoutAccountView(state: PayoutAccountState | null): PayoutAccountView {
  if (!state || !state.account_id) {
    return { status: "no_account", state: state ?? ({} as PayoutAccountState) }
  }
  if (state.ready) return { status: "ready", state }
  if (state.requirements_status === "restricted" || state.disabled_reason) {
    return { status: "restricted", state }
  }
  return { status: "incomplete", state }
}

function token() {
  if (typeof window === "undefined") return ""
  return localStorage.getItem("agent_token") || ""
}

function clearAgentSession() {
  if (typeof window === "undefined") return
  localStorage.removeItem("agent_token")
  localStorage.removeItem("agent_username")
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  const auth = token()
  if (auth) headers.set("Authorization", `Bearer ${auth}`)
  if (!(init?.body instanceof FormData)) headers.set("Content-Type", "application/json")

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers, cache: "no-store" })
  if (res.status === 401) {
    clearAgentSession()
    if (typeof window !== "undefined") window.location.href = "/agent-login"
    throw new Error("Agent session expired")
  }
  if (!res.ok) {
    const body = await res.text().catch(() => "")
    throw new Error(body || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function getAgentProfile() {
  const raw = await request<any>("/api/v1/agent/profile")
  return {
    agent_id: raw.agent_id,
    name: raw.name || "Agent",
    email: raw.email,
    license_type: raw.license_type,
    license_number: raw.license_number,
    states: raw.states || raw.license_states || [],
    languages: raw.languages || [],
    specialties: raw.specialties || [],
  } satisfies AgentProfile
}

export function saveAgentProfile(profile: Partial<AgentProfile>) {
  return request<any>("/api/v1/agent/profile", {
    method: "PATCH",
    body: JSON.stringify({
      name: profile.name,
      license_type: profile.license_type,
      license_states: profile.states,
      specialties: profile.specialties,
      languages: profile.languages,
    }),
  }).then((raw) => ({ ...profile, ...raw, states: raw.states || raw.license_states || profile.states || [] } as AgentProfile))
}

export async function listKnowledgeDocuments() {
  const raw = await request<any>("/api/v1/agent/knowledge")
  return {
    documents: (raw.documents || []).map((doc: any) => ({
      id: doc.id,
      name: doc.name || doc.filename,
      type: doc.type || doc.file_type,
      size: doc.size,
      status: doc.status,
      chunks: doc.chunks ?? doc.chunk_count,
      uploaded_at: doc.uploaded_at,
    } satisfies KnowledgeDocument)),
  }
}

export function uploadKnowledgeDocument(file: File) {
  const form = new FormData()
  form.append("file", file)
  return request<any>("/api/v1/agent/knowledge/upload", {
    method: "POST",
    body: form,
  }).then((raw) => ({
    document: {
      id: raw.document.id,
      name: raw.document.name || raw.document.filename,
      type: raw.document.type || raw.document.file_type,
      size: raw.document.size,
      status: raw.document.status,
      chunks: raw.document.chunks ?? raw.document.chunk_count,
      uploaded_at: raw.document.uploaded_at,
    } as KnowledgeDocument,
  }))
}

export function deleteKnowledgeDocument(id: string) {
  return request<{ ok: boolean }>(`/api/v1/agent/knowledge/${encodeURIComponent(id)}`, {
    method: "DELETE",
  })
}

export async function getAgentPreferences() {
  const raw = await request<any>("/api/v1/agent/preferences")
  return {
    response_style: raw.response_style || "consultative",
    priorities: raw.priorities || raw.preferred_topics || [],
    preferred_products: raw.preferred_products || [],
    preferred_carriers: raw.preferred_carriers || [],
    language_mode: raw.language_mode || raw.default_language || "auto",
    custom_instructions: raw.custom_instructions || raw.notes || "",
  } satisfies AgentPreferences
}

export function saveAgentPreferences(preferences: AgentPreferences) {
  return request<any>("/api/v1/agent/preferences", {
    method: "PUT",
    body: JSON.stringify({
      response_style: preferences.response_style,
      preferred_topics: preferences.priorities,
      preferred_products: preferences.preferred_products,
      preferred_carriers: preferences.preferred_carriers,
      default_language: preferences.language_mode,
      notes: preferences.custom_instructions,
    }),
  }).then(() => preferences)
}

export async function listAgentLeads() {
  const raw = await request<any>("/api/v1/agent/leads")
  return {
    leads: (raw.leads || []).map((lead: any) => ({
      id: lead.id || lead.lead_id,
      category: lead.category,
      summary: lead.summary,
      status: lead.status === "open" ? "available" : lead.status === "matched" ? "accepted" : lead.status,
      created_at: lead.created_at,
      client_region: lead.client_region || lead.location,
    } satisfies AgentLead)),
  }
}

export function acceptAgentLead(id: string) {
  return request<any>(`/api/v1/agent/leads/${encodeURIComponent(id)}/accept`, { method: "POST" }).then((lead) => ({
    id: lead.id || lead.lead_id || id,
    category: lead.category || "",
    summary: lead.summary || "",
    status: "accepted",
    created_at: lead.created_at,
    client_region: lead.client_region || lead.location,
  } as AgentLead))
}

export function declineAgentLead(id: string) {
  return request<any>(`/api/v1/agent/leads/${encodeURIComponent(id)}/decline`, { method: "POST" }).then((lead) => ({
    id: lead.id || lead.lead_id || id,
    category: lead.category || "",
    summary: lead.summary || "",
    status: "declined",
    created_at: lead.created_at,
    client_region: lead.client_region || lead.location,
  } as AgentLead))
}

export function listAgentSkills() {
  return request<{ skills: AgentSkill[] }>("/api/v1/agent/skills")
}

export function setAgentSkillEnabled(id: string, enabled: boolean) {
  return request<AgentSkill>(`/api/v1/agent/skills/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify({ enabled }),
  })
}

export function previewAgentAI(payload: AgentAIPreviewRequest) {
  return request<AgentAIPreviewResponse>("/api/v1/agent/ai-preview", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}
