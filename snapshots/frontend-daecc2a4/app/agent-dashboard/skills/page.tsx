"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { AgentSkill, listAgentSkills, setAgentSkillEnabled } from "../../lib/agent-console"

export default function AgentSkillsPage() {
  const router = useRouter()
  const [skills, setSkills] = useState<AgentSkill[]>([])
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState("")
  const [notice, setNotice] = useState("")

  useEffect(() => {
    if (!localStorage.getItem("agent_token")) {
      router.push("/agent-login")
      return
    }
    listAgentSkills()
      .then((res) => setSkills(res.skills || []))
      .catch(() => setNotice("Skill API is being integrated. This page defines the Agent Skill management contract."))
      .finally(() => setLoading(false))
  }, [router])

  async function toggle(skill: AgentSkill) {
    setBusyId(skill.id)
    setNotice("")
    try {
      const updated = await setAgentSkillEnabled(skill.id, !skill.enabled)
      setSkills((items) => items.map((item) => item.id === skill.id ? updated : item))
    } catch {
      setNotice("Skill status is not yet persisted to the DO backend; please wait for the backend API.")
    } finally {
      setBusyId("")
    }
  }

  return (
    <main style={{ minHeight: "100vh", background: "#0d0b12", color: "#f7f4ff", fontFamily: "Inter,system-ui,sans-serif" }}>
      <div style={{ maxWidth: 1180, margin: "0 auto", padding: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, marginBottom: 22 }}>
          <div>
            <button onClick={() => router.push("/agent-dashboard")} style={{ border: 0, background: "transparent", color: "#9d92aa", cursor: "pointer", padding: 0, marginBottom: 8 }}>← Agent Console</button>
            <h1 style={{ margin: 0, fontSize: 28 }}>Professional Skill Management</h1>
            <p style={{ color: "#9f98aa", marginTop: 8 }}>Control which professional Skills your AI can use and review each Skill&apos;s knowledge coverage.</p>
          </div>
          <button onClick={() => router.push("/agent-dashboard/ai-lab")} style={{ border: "1px solid #4b3d70", borderRadius: 10, padding: "10px 14px", background: "#201a31", color: "#d8cbff", cursor: "pointer", fontWeight: 700 }}>Open AI Lab</button>
        </div>

        {notice && <div style={{ marginBottom: 18, padding: 12, borderRadius: 10, background: "#181321", border: "1px solid #3b3151", color: "#cdbdf6", fontSize: 13 }}>{notice}</div>}

        {loading ? <div style={{ padding: 24, border: "1px solid #2d2936", borderRadius: 14, color: "#918a9b" }}>Loading Skills…</div> : null}

        {!loading && skills.length === 0 ? (
          <div style={{ padding: 28, border: "1px dashed #373140", borderRadius: 14, color: "#8f8798" }}>
            The backend has not returned the Skill list yet. The first official Skill is &quot;Life Protection Planning V1&quot;.
          </div>
        ) : null}

        <div style={{ display: "grid", gap: 14 }}>
          {skills.map((skill) => (
            <section key={skill.id} style={{ padding: 20, borderRadius: 16, border: "1px solid #2d2937", background: "#17141d" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 18, alignItems: "flex-start", flexWrap: "wrap" }}>
                <div style={{ flex: 1, minWidth: 240 }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                    <h2 style={{ margin: 0, fontSize: 18 }}>{skill.name}</h2>
                    <span style={{ fontSize: 11, color: "#9b8dca", border: "1px solid #40345b", borderRadius: 999, padding: "3px 8px" }}>{skill.version || "V1"}</span>
                    <span style={{ fontSize: 11, color: "#a49bad" }}>{skill.domain}</span>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 10, marginTop: 16 }}>
                    <Metric label="Knowledge Docs" value={String(skill.knowledge_document_count)} />
                    <Metric label="Knowledge Chunks" value={String(skill.knowledge_chunk_count)} />
                    <Metric label="Coverage" value={skill.coverage_status === "ready" ? "Ready" : skill.coverage_status === "partial" ? "Partial" : "Empty"} />
                  </div>
                  {skill.missing_knowledge?.length ? <div style={{ marginTop: 14, color: "#d7b96e", fontSize: 12 }}>Suggested additions:{skill.missing_knowledge.join(" · ")}</div> : null}
                </div>
                <button disabled={busyId === skill.id} onClick={() => void toggle(skill)} style={{ minWidth: 108, border: `1px solid ${skill.enabled ? "#426850" : "#4a4354"}`, borderRadius: 10, padding: "9px 13px", background: skill.enabled ? "#173522" : "#201d25", color: skill.enabled ? "#9ee6b3" : "#b6afbd", cursor: "pointer", fontWeight: 700 }}>{busyId === skill.id ? "Processing…" : skill.enabled ? "Enabled" : "Not Enabled"}</button>
              </div>
            </section>
          ))}
        </div>
      </div>
    </main>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div style={{ padding: 12, borderRadius: 11, border: "1px solid #292430", background: "#111017" }}><div style={{ fontSize: 11, color: "#837c8b" }}>{label}</div><div style={{ marginTop: 5, fontSize: 17, fontWeight: 750 }}>{value}</div></div>
}
