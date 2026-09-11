"use client"

import { useMemo, useState } from "react"
import { LIFE_INSURANCE_SKILL_V1, getMissingRequiredFields, isConnectionTrigger } from "../lib/professional-skills"

export default function AgentSkillEnginePage() {
  const skill = LIFE_INSURANCE_SKILL_V1
  const [facts, setFacts] = useState<Record<string, string>>({
    insured_person: "Myself",
    age: "45",
    coverage_goal: "身故保障",
    budget_amount: "2000",
    budget_period: "Monthly",
    responsibility_period: "10年",
    product_preference: "IUL",
  })
  const [message, setMessage] = useState("Connect with a licensed broker")

  const missing = useMemo(() => getMissingRequiredFields(skill, facts), [facts, skill])
  const triggered = useMemo(() => isConnectionTrigger(skill, message), [message, skill])
  const ready = missing.length === 0 || triggered

  function updateFact(key: string, value: string) {
    setFacts((current) => ({ ...current, [key]: value }))
  }

  return (
    <main style={{ minHeight: "100vh", background: "#0d0b12", color: "#f5f3ff", fontFamily: "Inter,system-ui,sans-serif", padding: 28 }}>
      <div style={{ maxWidth: 1180, margin: "0 auto" }}>
        <div style={{ marginBottom: 24 }}>
          <div style={{ color: "#9d7cff", fontSize: 12, fontWeight: 800 }}>GOAA PROFESSIONAL SKILL ENGINE</div>
          <h1 style={{ margin: "8px 0 6px", fontSize: 30 }}>{skill.name} <span style={{ color: "#8f8999", fontSize: 16 }}>v{skill.version}</span></h1>
          <p style={{ color: "#aaa4b5", lineHeight: 1.7, maxWidth: 820 }}>{skill.description}</p>
        </div>

        <section style={{ display: "grid", gridTemplateColumns: "1.05fr .95fr", gap: 18 }}>
          <div style={{ background: "#17151e", border: "1px solid #2a2734", borderRadius: 16, padding: 20 }}>
            <h2 style={{ marginTop: 0, fontSize: 18 }}>Guide Fields</h2>
            <div style={{ display: "grid", gap: 10 }}>
              {skill.fields.map((field) => (
                <label key={field.key} style={{ display: "grid", gridTemplateColumns: "170px 1fr", gap: 12, alignItems: "center", padding: "9px 0", borderBottom: "1px solid #24212c" }}>
                  <span style={{ fontSize: 13, color: field.required_for_ready ? "#fff" : "#9993a4" }}>{field.label}{field.required_for_ready ? " *" : ""}</span>
                  <input value={facts[field.key] || ""} onChange={(e) => updateFact(field.key, e.target.value)} placeholder={field.notes || ""} style={{ background: "#100e15", color: "#fff", border: "1px solid #34303d", borderRadius: 9, padding: "9px 10px" }} />
                </label>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gap: 18, alignContent: "start" }}>
            <div style={{ background: "#17151e", border: "1px solid #2a2734", borderRadius: 16, padding: 20 }}>
              <h2 style={{ marginTop: 0, fontSize: 18 }}>Loop Decider</h2>
              <label style={{ display: "block", fontSize: 12, color: "#9993a4", marginBottom: 7 }}>Current User Message</label>
              <textarea value={message} onChange={(e) => setMessage(e.target.value)} style={{ width: "100%", minHeight: 82, boxSizing: "border-box", background: "#100e15", color: "#fff", border: "1px solid #34303d", borderRadius: 10, padding: 11 }} />
              <div style={{ marginTop: 14, padding: 14, borderRadius: 12, background: ready ? "#102319" : "#251d0f", border: `1px solid ${ready ? "#245a39" : "#614a1e"}` }}>
                <div style={{ fontSize: 12, color: ready ? "#86efac" : "#fcd34d" }}>STATE</div>
                <div style={{ fontWeight: 800, fontSize: 22, marginTop: 5 }}>{triggered ? "CONNECTION_READY" : ready ? "READY" : "CLARIFY"}</div>
                <div style={{ color: "#a9a2b4", fontSize: 12, marginTop: 7 }}>{triggered ? "The customer explicitly asked to proceed; stop asking and generate the Need Package." : missing.length ? `Still missing: ${missing.join(", ")}` : "Required fields are satisfied; a need package can be formed."}</div>
              </div>
            </div>

            <div style={{ background: "#17151e", border: "1px solid #2a2734", borderRadius: 16, padding: 20 }}>
              <h2 style={{ marginTop: 0, fontSize: 18 }}>Knowledge Routing</h2>
              {skill.knowledge_layers.map((layer, index) => <div key={layer} style={{ display: "flex", gap: 10, padding: "8px 0", color: index < 4 ? "#d9d4df" : "#928b9d" }}><b style={{ color: "#8f73e8" }}>{index + 1}</b><span>{layer}</span></div>)}
            </div>

            <div style={{ background: "#17151e", border: "1px solid #2a2734", borderRadius: 16, padding: 20 }}>
              <h2 style={{ marginTop: 0, fontSize: 18 }}>Hard Stop Rules</h2>
              {skill.stop_rules.map((rule) => <div key={rule} style={{ fontSize: 13, color: "#b9b2c6", padding: "7px 0" }}>• {rule}</div>)}
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
