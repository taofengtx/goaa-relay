"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { previewAgentAI, AgentAIPreviewResponse } from "../../lib/agent-console"
import { LIFE_INSURANCE_SKILL_V1, getMissingRequiredFields, isConnectionTrigger } from "../../lib/professional-skills"

const demoFacts: Record<string, unknown> = {
  insured_person: "Myself",
  age: 45,
  coverage_goal: "Death Benefit",
  budget_amount: 2000,
  budget_period: "Monthly",
  responsibility_period: "10 years",
  product_preference: "IUL",
  currency: "unknown",
}

function localPreview(message: string, facts: Record<string, unknown>): AgentAIPreviewResponse {
  const missing = getMissingRequiredFields(LIFE_INSURANCE_SKILL_V1, facts)
  const triggered = isConnectionTrigger(LIFE_INSURANCE_SKILL_V1, message)
  const readyCount = LIFE_INSURANCE_SKILL_V1.fields.filter((field) => field.required_for_ready && facts[field.key] !== undefined && facts[field.key] !== null && facts[field.key] !== "").length
  const ready = readyCount >= LIFE_INSURANCE_SKILL_V1.readiness.minimum_required_fields
  const stage = triggered ? "connection_ready" : ready ? "ready" : missing.length ? "clarify" : "discovery"

  return {
    stage,
    connection_ready: triggered,
    response: triggered
      ? "Current request is ready for handoff. The system stops asking, prepares the Need Package, and shows the $39.90 professional connection entry."
      : ready
        ? "Information is sufficient for handoff. AI may answer follow-up questions but must not start new collection loops."
        : `Still needed: ${missing.join(", ") || "core goal"}.`,
    known_facts: facts,
    missing_fields: missing,
    need_package: triggered ? { ...facts, skill_id: LIFE_INSURANCE_SKILL_V1.id, status: "connection_ready" } : undefined,
    sources: [
      { layer: "platform_skill", label: "Life Insurance Skill V1" },
      { layer: "platform_knowledge", label: "Platform Standard Life Knowledge Base (awaiting backend)" },
      { layer: "agent_private_knowledge", label: "Current Agent Private Knowledge Base (awaiting backend)" },
      { layer: "agent_preferences", label: "Current Agent Answer Preferences (awaiting backend)" },
    ],
    applied_preferences: [],
  }
}

export default function AgentAILab() {
  const router = useRouter()
  const [message, setMessage] = useState("Connect with a Licensed Professional")
  const [factsText, setFactsText] = useState(JSON.stringify(demoFacts, null, 2))
  const [result, setResult] = useState<AgentAIPreviewResponse>(() => localPreview("Connect with a Licensed Professional", demoFacts))
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<"local" | "backend">("local")
  const [notice, setNotice] = useState("Currently using frontend Skill Engine rule preview; real RAG and Agent preference results appear once the DO backend is connected.")

  useEffect(() => {
    const token = localStorage.getItem("agent_token")
    if (!token) router.push("/agent-login")
  }, [router])

  const facts = useMemo(() => {
    try { return JSON.parse(factsText) as Record<string, unknown> } catch { return null }
  }, [factsText])

  async function runPreview() {
    if (!facts) {
      setNotice("Known Facts JSON format is invalid.")
      return
    }
    setLoading(true)
    try {
      const backend = await previewAgentAI({ skill_id: LIFE_INSURANCE_SKILL_V1.id, message, known_facts: facts })
      setResult(backend)
      setMode("backend")
      setNotice("Using DO backend real Agent AI Preview. Sources should show actual platform/private knowledge hits.")
    } catch {
      const local = localPreview(message, facts)
      setResult(local)
      setMode("local")
      setNotice("DO /api/v1/agent/ai-preview is not connected yet; using local Skill Engine rules for state-machine preview.")
    } finally {
      setLoading(false)
    }
  }

  function loadRegression001() {
    setMessage("Connect with a Licensed Professional")
    setFactsText(JSON.stringify(demoFacts, null, 2))
    setResult(localPreview("Connect with a Licensed Professional", demoFacts))
    setMode("local")
    setNotice("Loaded Regression Case #001 final handoff node. Expected: CONNECTION_READY; no further questions allowed.")
  }

  return (
    <main style={{ minHeight: "100vh", background: "#0d0b12", color: "#f5f3ff", fontFamily: "Inter,system-ui,sans-serif" }}>
      <div style={{ maxWidth: 1280, margin: "0 auto", padding: "26px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, marginBottom: 22 }}>
          <div>
            <button onClick={() => router.push("/agent-dashboard")} style={{ border: 0, background: "transparent", color: "#9d8bd4", cursor: "pointer", padding: 0 }}>← Agent Console</button>
            <h1 style={{ margin: "10px 0 6px", fontSize: 30 }}>My GOAA Agent · AI Lab</h1>
            <div style={{ color: "#918a9b", fontSize: 13 }}>Test skill behavior, knowledge retrieval, agent preferences, and professional handoff logic.</div>
          </div>
          <div style={{ padding: "8px 12px", border: "1px solid #3b3253", borderRadius: 10, background: "#171321", color: mode === "backend" ? "#86efac" : "#fbbf24", fontSize: 12 }}>● {mode === "backend" ? "DO REAL PREVIEW" : "LOCAL RULE PREVIEW"}</div>
        </div>

        <div style={{ padding: 13, border: "1px solid #3b3253", borderRadius: 12, background: "#171321", color: "#c8baf0", fontSize: 13, marginBottom: 18 }}>{notice}</div>

        <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(330px,.8fr)", gap: 18 }}>
          <section style={{ background: "#17151e", border: "1px solid #2a2734", borderRadius: 16, padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
              <div><div style={{ color: "#a993f3", fontSize: 12, fontWeight: 800 }}>ACTIVE SKILL</div><h2 style={{ margin: "5px 0 0", fontSize: 19 }}>{LIFE_INSURANCE_SKILL_V1.name} <span style={{ color: "#777181", fontSize: 12 }}>v{LIFE_INSURANCE_SKILL_V1.version}</span></h2></div>
              <button onClick={loadRegression001} style={{ border: "1px solid #41385d", borderRadius: 9, background: "#211a30", color: "#d9cef8", padding: "8px 11px", cursor: "pointer" }}>Load Case #001</button>
            </div>

            <label style={{ display: "block", marginTop: 20, color: "#a8a1b2", fontSize: 12 }}>Latest Customer Message</label>
            <input value={message} onChange={(e) => setMessage(e.target.value)} style={{ marginTop: 7, width: "100%", boxSizing: "border-box", border: "1px solid #373140", borderRadius: 10, background: "#100e15", color: "#fff", padding: "12px 13px", outline: "none" }} />

            <label style={{ display: "block", marginTop: 16, color: "#a8a1b2", fontSize: 12 }}>Known Facts</label>
            <textarea value={factsText} onChange={(e) => setFactsText(e.target.value)} rows={16} spellCheck={false} style={{ marginTop: 7, width: "100%", boxSizing: "border-box", border: facts ? "1px solid #373140" : "1px solid #7f1d1d", borderRadius: 10, background: "#100e15", color: "#d9d4df", padding: 13, outline: "none", fontFamily: "ui-monospace,SFMono-Regular,monospace", fontSize: 12, lineHeight: 1.55 }} />

            <button onClick={() => void runPreview()} disabled={loading} style={{ marginTop: 15, width: "100%", border: 0, borderRadius: 11, background: loading ? "#514765" : "#7655df", color: "#fff", padding: "12px 14px", fontWeight: 800, cursor: loading ? "default" : "pointer" }}>{loading ? "Running Agent Pipeline…" : "Run Agent AI Preview"}</button>
          </section>

          <section style={{ display: "grid", gap: 14, alignContent: "start" }}>
            <div style={{ background: result.connection_ready ? "#17251d" : "#17151e", border: result.connection_ready ? "1px solid #2f6c45" : "1px solid #2a2734", borderRadius: 16, padding: 20 }}>
              <div style={{ color: "#8f8999", fontSize: 12 }}>STATE</div>
              <div style={{ fontSize: 26, fontWeight: 850, marginTop: 6, color: result.connection_ready ? "#86efac" : "#fff" }}>{result.stage.toUpperCase()}</div>
              {result.connection_ready && <div style={{ marginTop: 10, padding: 10, borderRadius: 9, background: "#102016", color: "#b7f7c8", fontSize: 12 }}>$39.90 CTA should appear · must not return CLARIFY</div>}
            </div>

            <div style={{ background: "#17151e", border: "1px solid #2a2734", borderRadius: 16, padding: 20 }}>
              <div style={{ color: "#8f8999", fontSize: 12 }}>EXPECTED AI BEHAVIOR</div>
              <div style={{ marginTop: 9, color: "#d8d2df", lineHeight: 1.65, fontSize: 13 }}>{result.response}</div>
              {(result.missing_fields?.length || 0) > 0 && <div style={{ marginTop: 12, color: "#fbbf24", fontSize: 12 }}>To confirm but not necessarily blocking handoff:{result.missing_fields?.join(" · ")}</div>}
            </div>

            <div style={{ background: "#17151e", border: "1px solid #2a2734", borderRadius: 16, padding: 20 }}>
              <div style={{ color: "#8f8999", fontSize: 12, marginBottom: 10 }}>KNOWLEDGE PIPELINE / SOURCES</div>
              <div style={{ display: "grid", gap: 8 }}>
                {result.sources.map((source, index) => <div key={`${source.layer}-${index}`} style={{ padding: 10, borderRadius: 9, border: "1px solid #302b38", background: "#111017" }}><div style={{ color: "#a993f3", fontSize: 10, textTransform: "uppercase" }}>{source.layer.split("_").join(" ")}</div><div style={{ marginTop: 4, color: "#cbc4d1", fontSize: 12 }}>{source.filename || source.label}{typeof source.score === "number" ? ` · score ${source.score.toFixed(3)}` : ""}</div></div>)}
              </div>
            </div>

            {result.need_package && <div style={{ background: "#17151e", border: "1px solid #2a2734", borderRadius: 16, padding: 20 }}><div style={{ color: "#8f8999", fontSize: 12 }}>NEED PACKAGE</div><pre style={{ margin: "10px 0 0", whiteSpace: "pre-wrap", color: "#cfc8d7", fontSize: 11, lineHeight: 1.55 }}>{JSON.stringify(result.need_package, null, 2)}</pre></div>}
          </section>
        </div>
      </div>
    </main>
  )
}
