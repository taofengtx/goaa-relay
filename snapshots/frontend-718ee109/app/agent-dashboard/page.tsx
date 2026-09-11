"use client"

import { ChangeEvent, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import {
  AgentLead,
  AgentPreferences,
  AgentProfile,
  KnowledgeDocument,
  PayoutAccountState,
  createPayoutAccountLink,
  declineAgentLead,
  deleteKnowledgeDocument,
  getAgentPreferences,
  getAgentProfile,
  getPayoutAccountState,
  listAgentLeads,
  listKnowledgeDocuments,
  payoutAccountView,
  saveAgentPreferences,
  uploadKnowledgeDocument,
  verifyPayoutAccount,
} from "../lib/agent-console"
import { OrderSummary, orderApi } from "../lib/order-api"

type Tab = "home" | "orders" | "ai" | "knowledge" | "account"
type OrderView = "pool" | "service"

const defaultPreferences: AgentPreferences = {
  response_style: "consultative",
  priorities: ["Protection", "Family Responsibilities"],
  preferred_products: [],
  preferred_carriers: [],
  language_mode: "auto",
  custom_instructions: "",
}

const shell: React.CSSProperties = { minHeight: "100vh", background: "#0d0b12", color: "#f7f5fb", fontFamily: "Inter,system-ui,sans-serif" }
const card: React.CSSProperties = { background: "#17151e", border: "1px solid #2b2734", borderRadius: 18, padding: 20 }
const input: React.CSSProperties = { width: "100%", boxSizing: "border-box", border: "1px solid #393342", borderRadius: 11, background: "#100e15", color: "#f7f5fb", padding: "11px 12px", outline: "none", fontFamily: "inherit" }
const primary: React.CSSProperties = { border: 0, borderRadius: 10, background: "#7655df", color: "white", padding: "10px 14px", fontWeight: 750, cursor: "pointer" }
const secondary: React.CSSProperties = { border: "1px solid #3b3545", borderRadius: 10, background: "transparent", color: "#c7c0cf", padding: "9px 13px", cursor: "pointer" }

export default function AgentDashboard() {
  const router = useRouter()
  const [tab, setTab] = useState<Tab>("home")
  const [orderView, setOrderView] = useState<OrderView>("pool")
  const [username, setUsername] = useState("Agent")
  const [profile, setProfile] = useState<AgentProfile | null>(null)
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [preferences, setPreferences] = useState<AgentPreferences>(defaultPreferences)
  const [leads, setLeads] = useState<AgentLead[]>([])
  const [serviceOrders, setServiceOrders] = useState<OrderSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState("")
  const [paywallLead, setPaywallLead] = useState<AgentLead | null>(null)
  const [payout, setPayout] = useState<PayoutAccountState | null>(null)
  const [payoutBusy, setPayoutBusy] = useState(false)
  const [payoutError, setPayoutError] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem("agent_token")
    if (!token) { router.replace("/agent-login"); return }
    setUsername(localStorage.getItem("agent_username") || "Agent")
    // Golden Candidate Final UX: onboarding return lands on the Agent Console
    // with only non-sensitive navigation context (?tab=account&order=...&onboarding=return).
    // Agent identity comes from the authenticated session; auto-verify + show
    // the payout account card. No bearer token in the URL.
    const sp = new URLSearchParams(window.location.search)
    if (sp.get("tab") === "account") { setTab("account") }
    if (sp.get("onboarding") === "return") {
      setTab("account")
      void autoVerifyOnboardingReturn()
    }
    void bootstrap()
  }, [router])

  async function autoVerifyOnboardingReturn() {
    setPayoutBusy(true)
    try {
      const r = await verifyPayoutAccount()
      setPayout(r.state)
      setPayoutError(false)
      setNotice(r.ready ? "Payout account ready ✅" : "Stripe onboarding is not complete — please finish the required steps.")
    } catch {
      setPayoutError(true)
      setNotice("Payout account verification is temporarily unavailable. Please try again later.")
    } finally {
      setPayoutBusy(false)
    }
  }

  async function loadPayout() {
    setPayoutError(false)
    try {
      setPayout(await getPayoutAccountState())
    } catch {
      // Card must never disappear: keep previous payout state and surface an
      // explicit error + reload action instead.
      setPayoutError(true)
    }
  }

  async function startPayoutOnboarding() {
    setPayoutBusy(true)
    setNotice("")
    try {
      const link = await createPayoutAccountLink()
      if (link.url) {
        window.location.href = link.url
        return
      }
      setNotice("Payout account is already ready.")
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Unable to create onboarding link. Please try again later.")
    } finally {
      setPayoutBusy(false)
    }
  }

  async function bootstrap() {
    setLoading(true)
    setNotice("")
    try {
      const [p, k, pref, l] = await Promise.all([getAgentProfile(), listKnowledgeDocuments(), getAgentPreferences(), listAgentLeads()])
      setProfile(p)
      setDocuments(k.documents || [])
      setPreferences(pref)
      setLeads(l.leads || [])
      // My Service Orders: formal Order Engine list scoped server-side to this
      // agent (GET /orders → WHERE agent_id = token user). Details fetched per
      // order so cards show real amount / settlement / invoice (no hardcode).
      try {
        const token = localStorage.getItem("agent_token") || ""
        const rows = await orderApi.listOrders(token)
        const ids = (rows.orders || []).map(r => String(r.id || "")).filter(Boolean)
        const details = await Promise.all(ids.map(id => orderApi.getOrder(id, token).catch(() => null)))
        setServiceOrders(details.filter((x): x is OrderSummary => !!x))
      } catch {
        setNotice("Service orders are temporarily unavailable. Please refresh.")
      }
    } catch {
      setNotice("Some data is temporarily unavailable. Please refresh.")
    } finally {
      setLoading(false)
      // Payout state loads independently so the payout card renders even if
      // other dashboard data fails.
      void loadPayout()
    }
  }

  const readyDocs = useMemo(() => documents.filter(d => d.status === "ready").length, [documents])
  const orderPool = useMemo(() => leads.filter(l => l.status !== "closed"), [leads])
  const wonOrders = useMemo(() => leads.filter(l => l.status === "closed"), [leads])
  const availableOrders = useMemo(() => leads.filter(l => l.status === "available").length, [leads])
  const inProgressOrders = useMemo(() => leads.filter(l => l.status === "accepted").length, [leads])
  const monthlyPushCount = useMemo(() => {
    const now = new Date()
    return leads.filter(l => {
      if (!l.created_at) return true
      const d = new Date(l.created_at)
      return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth()
    }).length
  }, [leads])
  // ── My Service Orders (formal Order Engine, grouped by business stage) ──
  const serviceStageLabel = useMemo(() => ({
    estimate: "Awaiting Customer Confirmation", accepted: "Estimate Accepted", paid: "Customer Paid",
    processing: "Service in Progress", waiting_customer: "Waiting for Customer Info",
    documents_complete: "Information Complete", delivery_submitted: "Deliverables Delivered",
    customer_review: "Awaiting Customer Confirmation", delivered: "Delivery Awaiting Confirmation",
    completed: "Completed", settled: "Settled",
  } as Record<string, string>), [])
  const followServiceOrders = useMemo(() => serviceOrders.filter(o => o.stage === "estimate" || o.stage === "accepted"), [serviceOrders])
  const activeServiceOrders = useMemo(() => serviceOrders.filter(o => ["paid", "processing", "waiting_customer", "documents_complete", "delivery_submitted", "customer_review", "delivered"].includes(o.stage)), [serviceOrders])
  const doneServiceOrders = useMemo(() => serviceOrders.filter(o => o.stage === "completed" || (o.dbStage && ["settled", "completed"].includes(o.dbStage))), [serviceOrders])
  const aiReady = readyDocs > 0
  const displayOrders = orderView === "pool" ? orderPool : []

  async function releaseOrder(id: string) {
    setBusy(true)
    try {
      const updated = await declineAgentLead(id)
      setLeads(items => items.map(x => x.id === id ? updated : x))
      setNotice("You passed on this opportunity. It stays in the Opportunity Pool so other professionals can be matched.")
    } catch {
      setNotice("Action failed. Please try again.")
    } finally {
      setBusy(false)
    }
  }

  async function handleUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ""
    if (!file) return
    if (!/\.(pdf|txt|docx|pptx)$/i.test(file.name)) { setNotice("Currently supported: PDF, DOCX, PPTX, and TXT."); return }
    setBusy(true)
    setNotice("Your AI is learning from this document…")
    try {
      const r = await uploadKnowledgeDocument(file)
      setDocuments(items => [r.document, ...items.filter(x => x.id !== r.document.id)])
      setNotice("Document uploaded. Your AI will reference it once it has finished learning.")
    } catch {
      setNotice("Upload failed. Please try again.")
    } finally {
      setBusy(false)
    }
  }

  async function removeDocument(id: string) {
    setBusy(true)
    try {
      await deleteKnowledgeDocument(id)
      setDocuments(x => x.filter(d => d.id !== id))
      setNotice("This document was removed from your AI knowledge base.")
    } catch {
      setNotice("Delete failed. Please try again.")
    } finally {
      setBusy(false)
    }
  }

  async function savePreferences() {
    setBusy(true)
    try {
      setPreferences(await saveAgentPreferences(preferences))
      setNotice("Saved. Your AI will follow these preferences when talking with customers.")
    } catch {
      setNotice("Save failed. Please try again.")
    } finally {
      setBusy(false)
    }
  }

  function openAIMediation() {
    setNotice("Customer communication is relayed through GOAA AI. Contact details are never shown in the Agent workspace.")
  }

  function logout() {
    localStorage.removeItem("agent_token")
    localStorage.removeItem("agent_username")
    localStorage.removeItem("agent_id")
    router.replace("/agent-login")
  }

  // ═══ Payout account (Stripe Connect) ═══
  // Golden Candidate Final UX: no bearer token input; account creation and
  // readiness are driven by the Agent onboarding flow + server-side verify.
  function renderPayoutCard() {
    // The payout card must ALWAYS render. On API failure show an explicit
    // error state with a reload action instead of hiding the section.
    if (payoutError) {
      return (
        <div style={card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
            <div>
              <div style={{ color: "#8f8999", fontSize: 12, fontWeight: 800 }}>Payout Account</div>
              <div style={{ color: "#fca5a5", fontSize: 13, marginTop: 9, lineHeight: 1.6 }}>Unable to read payout account status. Please try again later.</div>
            </div>
            <button disabled={payoutBusy} onClick={() => void loadPayout()} style={secondary}>Reload</button>
          </div>
        </div>
      )
    }
    const view = payoutAccountView(payout)
    const chipColor =
      view.status === "ready" ? "#86efac" :
      view.status === "no_account" ? "#fcd34d" :
      view.status === "restricted" ? "#fca5a5" : "#93c5fd"
    const chipLabel =
      view.status === "ready" ? "Payout Account Ready" :
      view.status === "no_account" ? "Not Set Up" :
      view.status === "restricted" ? "Restricted" : "Onboarding Pending"
    const actionLabel =
      view.status === "ready" ? "Check Status" :
      view.status === "incomplete" ? "Finish Onboarding" : "Set Up Payout"
    const desc =
      view.status === "ready" ? "Stripe Express payout account is active and ready to receive service fee settlements."
      : view.status === "restricted" ? (view.state.disabled_reason ? `Account restricted: ${view.state.disabled_reason}` : "Account restricted. Resolve the issue in Stripe to continue.")
      : view.status === "incomplete" ? "Stripe onboarding is not complete — finish the required steps to verify automatically."
      : "Once set up, you will receive settlement payouts after services complete."
    return (
      <div style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
          <div>
            <div style={{ color: "#8f8999", fontSize: 12, fontWeight: 800 }}>Payout Account</div>
            <div style={{ display: "flex", alignItems: "center", gap: 9, marginTop: 7 }}>
              <span style={{ fontSize: 13, fontWeight: 800, color: chipColor, border: `1px solid ${chipColor}55`, borderRadius: 20, padding: "4px 11px", background: `${chipColor}14` }}>{chipLabel}</span>
              {payoutBusy && <span style={{ fontSize: 12, color: "#8d8799" }}>Syncing…</span>}
            </div>
            <div style={{ color: "#9993a4", fontSize: 13, marginTop: 9, lineHeight: 1.6 }}>{desc}</div>
            {view.status === "restricted" && view.state.disabled_reason && (
              <div style={{ fontSize: 12, color: "#fca5a5", marginTop: 6 }}>Security note: only update information on Stripe official pages. Never enter passwords or secret keys anywhere else.</div>
            )}
          </div>
          <button disabled={payoutBusy} onClick={() => void startPayoutOnboarding()} style={{ ...primary, opacity: payoutBusy ? 0.55 : 1 }}>
            {actionLabel}
          </button>
        </div>
      </div>
    )
  }

  const nav: Array<[Tab, string]> = [["home", "Home"], ["orders", "Opportunities"], ["ai", "My AI"], ["knowledge", "Knowledge Base"], ["account", "Account"]]

  return <main style={shell}>
    <header style={{ borderBottom: "1px solid #211e29", background: "rgba(13,11,18,.96)", position: "sticky", top: 0, zIndex: 20 }}>
      <div style={{ maxWidth: 1280, margin: "0 auto", padding: "16px 24px", display: "flex", justifyContent: "space-between" }}>
        <div><div style={{ fontWeight: 850, fontSize: 21 }}>GOAA.ai <span style={{ color: "#9d7cff" }}>My Agent</span></div><div style={{ color: "#8d8799", fontSize: 12, marginTop: 3 }}>Your AI Professional Workspace</div></div>
        <div style={{ color: "#aaa4b5", fontSize: 13 }}>{profile?.name || username}</div>
      </div>
    </header>

    <div style={{ maxWidth: 1280, margin: "0 auto", padding: "22px 24px 64px" }}>
      <nav style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 22 }}>{nav.map(([id, label]) => <button key={id} onClick={() => setTab(id)} style={{ border: "1px solid #302b38", borderRadius: 10, padding: "9px 14px", cursor: "pointer", color: tab === id ? "#fff" : "#aaa3b5", background: tab === id ? "#6549c8" : "#15131b", fontWeight: 700 }}>{label}</button>)}</nav>
      {notice && <div style={{ marginBottom: 16, padding: "12px 14px", border: "1px solid #3c3156", borderRadius: 12, background: "#171321", color: "#cdbff7", fontSize: 13 }}>{notice}</div>}
      {loading && <div style={{ ...card, color: "#9b95a5" }}>Opening your workspace…</div>}

      {!loading && tab === "home" && <section style={{ display: "grid", gap: 16 }}>
        <div style={{ ...card, padding: 26, background: "linear-gradient(145deg,#211735,#15121d)", borderColor: "#40345d" }}>
          <div style={{ color: "#a993f3", fontWeight: 800, fontSize: 12 }}>MY GOAA AGENT</div>
          <h1 style={{ margin: "9px 0 8px", fontSize: 30 }}>Start with what matters most today</h1>
          <p style={{ margin: 0, color: "#aaa4b5", lineHeight: 1.7 }}>GOAA.ai keeps sending opportunities matched to your specialty. Push history is retained so you can see real demand frequency.</p>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(210px,1fr))", gap: 14 }}>
          <StatusCard label="Opportunities This Month" value={String(monthlyPushCount)} sub={`${availableOrders} priority now · ${orderPool.length} in pool`} />
          <StatusCard label="Completed Orders" value={String(doneServiceOrders.length)} sub="Completed / settled service orders" />
          <StatusCard label="My AI" value={aiReady ? "Learning Started" : "Not Trained"} sub={aiReady ? `Learned from ${readyDocs} documents` : "Upload a document to get started"} />
          <StatusCard label="Specialty" value={profile?.specialties?.[0] || "Incomplete"} sub={profile?.specialties?.slice(1).join(" · ") || "Add in your account profile"} />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))", gap: 14 }}>
          <ActionCard title="My Service Orders" copy={`You have ${serviceOrders.length} service order(s): in-progress, active, completed, and settled all appear here.`} action="View Service Orders" onClick={() => { setOrderView("service"); setTab("orders") }} />
          <ActionCard title="Opportunity Pool" copy="New, pending, passed, and referred opportunities all stay here." action="View Opportunity Pool" onClick={() => { setOrderView("pool"); setTab("orders") }} />
          <ActionCard title={aiReady ? "Test My AI" : "Teach My AI First"} copy={aiReady ? "See how your AI answers real customer questions." : "Upload product manuals, underwriting guides, or your own Q&A."} action={aiReady ? "Test My AI" : "Upload Materials"} onClick={() => aiReady ? router.push("/agent-dashboard/ai-lab") : setTab("knowledge")} />
          <ActionCard title="Teach AI to Communicate My Way" copy="Set response style, language, and priorities." action="Configure My AI" onClick={() => setTab("ai")} />
        </div>
      </section>}

      {!loading && tab === "orders" && <section style={{ display: "grid", gap: 14 }}>
        <div><h1 style={{ margin: 0, fontSize: 28 }}>Opportunities</h1><p style={{ color: "#9993a4", marginTop: 6 }}>The Opportunity Pool shows opportunities pushed to you (awaiting decision / accept / pass). My Service Orders come from the service order system and include every order you are bound to. Customer contact details are never shown here.</p></div>
        <div style={{ ...card, padding: 16, display: "flex", gap: 20, flexWrap: "wrap" }}>
          <div><div style={{ color: "#8f8999", fontSize: 11 }}>This Month</div><div style={{ fontSize: 22, fontWeight: 800, marginTop: 4 }}>{monthlyPushCount}</div></div>
          <div><div style={{ color: "#8f8999", fontSize: 11 }}>Awaiting Decision</div><div style={{ fontSize: 22, fontWeight: 800, marginTop: 4 }}>{availableOrders}</div></div>
          <div><div style={{ color: "#8f8999", fontSize: 11 }}>In Service</div><div style={{ fontSize: 22, fontWeight: 800, marginTop: 4 }}>{activeServiceOrders.length}</div></div>
          <div><div style={{ color: "#8f8999", fontSize: 11 }}>Completed</div><div style={{ fontSize: 22, fontWeight: 800, marginTop: 4 }}>{doneServiceOrders.length}</div></div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setOrderView("pool")} style={orderView === "pool" ? primary : secondary}>Opportunity Pool {orderPool.length}</button>
          <button onClick={() => setOrderView("service")} style={orderView === "service" ? primary : secondary}>My Service Orders {serviceOrders.length}</button>
        </div>
        {orderView === "pool" && (displayOrders.length === 0 ? <Empty text="No opportunities yet." /> : displayOrders.map((lead, i) => <article key={lead.id} style={{ ...card, borderColor: lead.status === "available" && i === 0 ? "#5b46a0" : "#2b2734" }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 18, alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <span style={{ color: "#a88af7", fontSize: 12, fontWeight: 800 }}>{friendlyCategory(lead.category)}</span>
                <OrderStatus status={lead.status} />
                {lead.status === "available" && i === 0 && <span style={{ fontSize: 11, padding: "4px 8px", borderRadius: 20, background: "#2b2146", color: "#cbb9ff" }}>Priority Match</span>}
              </div>
              <div style={{ marginTop: 9, fontSize: 19, fontWeight: 750, lineHeight: 1.5 }}>{cleanLeadSummary(lead.summary)}</div>
              <div style={{ marginTop: 9, color: "#928c9d", fontSize: 12 }}>{lead.client_region || "Region TBD"}{lead.created_at ? ` · Pushed ${formatDate(lead.created_at)}` : ""}</div>
              <div style={{ marginTop: 12, color: "#aaa4b5", fontSize: 12 }}>🔒 Customer name, phone, email, and other contact details are never shown in the Agent workspace. Communication is relayed by GOAA AI.</div>
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {lead.status === "available" && <><button disabled={busy} onClick={() => void releaseOrder(lead.id)} style={secondary}>Pass</button><button onClick={() => setPaywallLead(lead)} style={primary}>Accept Opportunity</button></>}
              {lead.status === "accepted" && <><button onClick={openAIMediation} style={primary}>Message via AI</button><button disabled={busy} onClick={() => void releaseOrder(lead.id)} style={secondary}>No Deal / Refer</button></>}
              {lead.status === "declined" && <span style={{ padding: "9px 13px", borderRadius: 10, background: "#25212c", color: "#aaa4b5", fontWeight: 700 }}>Referred to Another Agent</span>}
              {lead.status === "closed" && <span style={{ padding: "9px 13px", borderRadius: 10, background: "#193523", color: "#86efac", fontWeight: 700 }}>Deal Reached</span>}
            </div>
          </div>
        </article>))}
        {orderView === "service" && (serviceOrders.length === 0 ? <Empty text="No service orders yet. Accept an opportunity from the Opportunity Pool and it will appear here." /> : <>
          {followServiceOrders.length > 0 && <ServiceGroup title={`In Progress · ${followServiceOrders.length}`} orders={followServiceOrders} stageLabel={serviceStageLabel} onOpen={id => router.push(`/agent-order-live?order=${id}`)} />}
          {activeServiceOrders.length > 0 && <ServiceGroup title={`Active · ${activeServiceOrders.length}`} orders={activeServiceOrders} stageLabel={serviceStageLabel} onOpen={id => router.push(`/agent-order-live?order=${id}`)} />}
          {doneServiceOrders.length > 0 && <ServiceGroup title={`Completed · ${doneServiceOrders.length}`} orders={doneServiceOrders} stageLabel={serviceStageLabel} onOpen={id => router.push(`/agent-order-live?order=${id}`)} />}
        </>)}
      </section>}

      {!loading && tab === "ai" && <section style={{ display: "grid", gap: 16 }}>
        <div><h1 style={{ margin: 0, fontSize: 26 }}>My AI</h1><p style={{ color: "#9993a4", marginTop: 6 }}>Tell your AI how you like to communicate with customers, then test it with real questions.</p></div>
        <div style={card}>
          <h2 style={{ marginTop: 0, fontSize: 18 }}>Teach My AI How to Speak</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: 14 }}>
            <Field label="Answer Style"><select value={preferences.response_style} onChange={e => setPreferences({ ...preferences, response_style: e.target.value as AgentPreferences["response_style"] })} style={input}><option value="concise">Concise</option><option value="detailed">Detailed & Professional</option><option value="educational">Educational</option><option value="consultative">Consultative</option></select></Field>
            <Field label="Language"><select value={preferences.language_mode} onChange={e => setPreferences({ ...preferences, language_mode: e.target.value as AgentPreferences["language_mode"] })} style={input}><option value="auto">Follow Customer</option><option value="zh">Chinese First</option><option value="en">English First</option></select></Field>
            <Field label="What I Prioritize"><input value={preferences.priorities.join(", ")} onChange={e => setPreferences({ ...preferences, priorities: splitValues(e.target.value) })} style={input} placeholder="Protection, Cash Value, Retirement, Legacy" /></Field>
            <Field label="Products I Know"><input value={preferences.preferred_products.join(", ")} onChange={e => setPreferences({ ...preferences, preferred_products: splitValues(e.target.value) })} style={input} placeholder="IUL, Term, Whole Life" /></Field>
          </div>
          <Field label="Carriers I Use"><input value={preferences.preferred_carriers.join(", ")} onChange={e => setPreferences({ ...preferences, preferred_carriers: splitValues(e.target.value) })} style={input} /></Field>
          <Field label="Special Notes for AI"><textarea value={preferences.custom_instructions} onChange={e => setPreferences({ ...preferences, custom_instructions: e.target.value })} style={{ ...input, minHeight: 110 }} /></Field>
          <div style={{ display: "flex", gap: 10 }}><button disabled={busy} onClick={() => void savePreferences()} style={primary}>Save Preferences</button><button onClick={() => router.push("/agent-dashboard/ai-lab")} style={secondary}>Test My AI</button></div>
        </div>
      </section>}

      {!loading && tab === "knowledge" && <section style={{ display: "grid", gap: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}><div><h1 style={{ margin: 0, fontSize: 26 }}>Knowledge Base</h1><p style={{ color: "#9993a4", marginTop: 6 }}>Upload product materials, underwriting guides, training documents, and Q&A so your AI keeps getting smarter.</p></div><label style={{ ...primary, display: "inline-flex", alignItems: "center" }}>{busy ? "Processing…" : "+ Upload Materials"}<input type="file" disabled={busy} onChange={handleUpload} accept=".pdf,.docx,.pptx,.txt" style={{ display: "none" }} /></label></div>
        <div style={card}>{documents.length === 0 ? <Empty text="No materials yet. Upload your first document and your AI will start learning." /> : <div style={{ display: "grid", gap: 10 }}>{documents.map(doc => <div key={doc.id} style={{ display: "flex", justifyContent: "space-between", gap: 14, padding: 14, border: "1px solid #2b2733", borderRadius: 12, background: "#121018" }}><div><div style={{ fontWeight: 700 }}>{doc.name}</div><div style={{ marginTop: 5, fontSize: 12, color: doc.status === "ready" ? "#86efac" : doc.status === "failed" ? "#fca5a5" : "#fcd34d" }}>{doc.status === "ready" ? "AI Learned" : doc.status === "processing" ? "AI Learning" : "Processing Failed"}</div></div><button disabled={busy} onClick={() => void removeDocument(doc.id)} style={secondary}>Delete</button></div>)}</div>}</div>
      </section>}

      {!loading && tab === "account" && <section style={{ display: "grid", gap: 16 }}>
        <div><h1 style={{ margin: 0, fontSize: 26 }}>Account</h1><p style={{ color: "#9993a4", marginTop: 6 }}>Review your professional profile and account information.</p></div>
        <div style={card}><Info label="Name" value={profile?.name || username} /><Info label="License Type" value={profile?.license_type || "Incomplete"} /><Info label="Licensed States" value={profile?.states?.join(" · ") || "Incomplete"} /><Info label="Specialty" value={profile?.specialties?.join(" · ") || "Incomplete"} /><Info label="Languages" value={profile?.languages?.join(" · ") || "Incomplete"} /><button onClick={logout} style={{ ...secondary, marginTop: 10 }}>Sign Out</button></div>
        {renderPayoutCard()}
      </section>}
    </div>

    {paywallLead && <div style={{ position: "fixed", inset: 0, zIndex: 100, background: "rgba(0,0,0,.72)", display: "grid", placeItems: "center", padding: 20 }} onClick={() => setPaywallLead(null)}>
      <div onClick={e => e.stopPropagation()} style={{ width: "min(520px,100%)", borderRadius: 20, padding: 24, background: "#181420", border: "1px solid #564180", boxShadow: "0 24px 80px rgba(0,0,0,.45)" }}>
        <div style={{ color: "#a993f3", fontSize: 12, fontWeight: 800 }}>GOAA AGENT PRO</div>
        <h2 style={{ margin: "8px 0 6px", fontSize: 26 }}>Unlock This Opportunity</h2>
        <p style={{ color: "#aaa4b5", lineHeight: 1.65 }}>With Agent Pro you get priority on this opportunity and ongoing matched opportunities for your license and specialty.</p>
        <div style={{ ...card, background: "#121018", margin: "16px 0" }}><div style={{ fontWeight: 750 }}>{cleanLeadSummary(paywallLead.summary)}</div><div style={{ color: "#928c9d", fontSize: 12, marginTop: 6 }}>{paywallLead.client_region || "Region TBD"}</div></div>
        <div style={{ display: "grid", gap: 8, color: "#d7d1df", fontSize: 13, lineHeight: 1.5 }}><span>✓ Priority on current opportunity</span><span>✓ Ongoing matched opportunities</span><span>✓ Dedicated My GOAA Agent AI</span><span>✓ Private knowledge base with personalized answers</span><span>✓ Customer messages relayed by GOAA AI to protect both sides</span></div>
        <div style={{ marginTop: 20, fontSize: 28, fontWeight: 850 }}>$99 <span style={{ fontSize: 13, color: "#9993a4", fontWeight: 500 }}>/month</span></div>
        <div style={{ display: "flex", gap: 10, marginTop: 16 }}><button onClick={() => setPaywallLead(null)} style={{ ...secondary, flex: 1 }}>Not Now</button><button onClick={() => { setNotice("Agent Pro $99 payment will connect to Stripe once commercial rules are confirmed; no charge today."); setPaywallLead(null) }} style={{ ...primary, flex: 1 }}>Set Up & Accept</button></div>
      </div>
    </div>}
  </main>
}

function ServiceGroup({ title, orders, stageLabel, onOpen }: { title: string; orders: OrderSummary[]; stageLabel: Record<string, string>; onOpen: (id: string) => void }) {
  return <div style={{ display: "grid", gap: 10 }}>
    <div style={{ color: "#8f8999", fontSize: 12, fontWeight: 800, letterSpacing: 1 }}>{title}</div>
    {orders.map(o => <ServiceOrderCard key={o.id} o={o} stageLabel={stageLabel} onClick={() => onOpen(o.id)} />)}
  </div>
}

function ServiceOrderCard({ o, stageLabel, onClick }: { o: OrderSummary; stageLabel: Record<string, string>; onClick: () => void }) {
  const amount = o.invoice?.amount ?? o.amount ?? 0
  const settled = o.settlement === "paid"
  const invoiced = !!o.invoice
  return <article onClick={onClick} style={{ ...card, cursor: "pointer", borderColor: "#2b2734" }}>
    <div style={{ display: "flex", justifyContent: "space-between", gap: 18, alignItems: "flex-start", flexWrap: "wrap" }}>
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ fontWeight: 800, fontSize: 16 }}>{o.serviceTitle || "Service Order"}</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
          <span style={{ padding: "5px 10px", borderRadius: 14, background: "#25212c", color: "#d7d1df", fontSize: 12, fontWeight: 700 }}>{stageLabel[o.stage] || o.stage}</span>
          {settled && <span style={{ padding: "5px 10px", borderRadius: 14, background: "#193523", color: "#86efac", fontSize: 12, fontWeight: 700 }}>✓ Settled</span>}
          {invoiced && <span style={{ padding: "5px 10px", borderRadius: 14, background: "#1d2a3a", color: "#93c5fd", fontSize: 12, fontWeight: 700 }}>Invoice Available</span>}
        </div>
        <div style={{ marginTop: 12, color: "#9993a4", fontSize: 12 }}>Open Service Workspace</div>
      </div>
      <div style={{ fontSize: 22, fontWeight: 850 }}>${amount.toFixed(2)}</div>
    </div>
  </article>
}

function StatusCard({ label, value, sub }: { label: string; value: string; sub: string }) { return <div style={card}><div style={{ color: "#8f8999", fontSize: 12 }}>{label}</div><div style={{ fontSize: 24, fontWeight: 800, marginTop: 8 }}>{value}</div><div style={{ color: "#8e8899", fontSize: 12, marginTop: 7, lineHeight: 1.5 }}>{sub}</div></div> }
function ActionCard({ title, copy, action, onClick }: { title: string; copy: string; action: string; onClick: () => void }) { return <article style={{ ...card, display: "flex", flexDirection: "column", minHeight: 165 }}><h2 style={{ margin: 0, fontSize: 18 }}>{title}</h2><p style={{ color: "#9993a4", lineHeight: 1.65, fontSize: 13, flex: 1 }}>{copy}</p><button onClick={onClick} style={{ ...primary, alignSelf: "flex-start" }}>{action}</button></article> }
function Empty({ text }: { text: string }) { return <div style={{ padding: 30, textAlign: "center", color: "#847e8e", border: "1px dashed #34303d", borderRadius: 12 }}>{text}</div> }
function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label style={{ display: "grid", gap: 7, marginBottom: 14 }}><span style={{ color: "#aaa3b5", fontSize: 12, fontWeight: 700 }}>{label}</span>{children}</label> }
function Info({ label, value }: { label: string; value: string }) { return <div style={{ padding: "12px 0", borderBottom: "1px solid #282431", display: "grid", gridTemplateColumns: "140px 1fr", gap: 18 }}><span style={{ color: "#8f8999" }}>{label}</span><span>{value}</span></div> }
function OrderStatus({ status }: { status: AgentLead["status"] }) {
  const map: Record<AgentLead["status"], [string, string, string]> = {
    available: ["Awaiting Decision", "#2b2146", "#cbb9ff"],
    accepted: ["In Progress", "#18334b", "#93c5fd"],
    declined: ["Referred", "#2a252d", "#aaa4b5"],
    closed: ["Deal Reached", "#193523", "#86efac"],
  }
  const [label, bg, color] = map[status]
  return <span style={{ fontSize: 11, padding: "4px 8px", borderRadius: 20, background: bg, color }}>{label}</span>
}
function splitValues(value: string) { return value.split(/[,，]/).map(item => item.trim()).filter(Boolean) }
function friendlyCategory(value: string) { return value === "insurance" ? "Financial Planning" : value || "Professional Need" }
function cleanLeadSummary(value: string) { return value.replace(/^life\s*/i, "Life ").replace(/available|accepted|matched|declined|closed/gi, "").replace(/\s+/g, " ").trim() }
function formatDate(value: string) { const d = new Date(value); return Number.isNaN(d.getTime()) ? value : `${d.getMonth() + 1}/${d.getDate()}` }
