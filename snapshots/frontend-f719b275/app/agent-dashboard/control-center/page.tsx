"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

const cards = [
  {
    title: "Today's Customer Needs",
    copy: "Review pending Need Packages and prioritize customers ready to connect with a professional.",
    action: "View Customer Needs",
    href: "/agent-dashboard",
  },
  {
    title: "My Professional Skills",
    copy: "Review enabled capabilities, knowledge coverage, and missing materials.",
    action: "Manage Skills",
    href: "/agent-dashboard/skills",
  },
  {
    title: "Train My GOAA Agent",
    copy: "Test answers with real customer questions and confirm your AI uses your private knowledge and preferences.",
    action: "Open AI Lab",
    href: "/agent-dashboard/ai-lab",
  },
  {
    title: "Grow My Knowledge Base",
    copy: "Upload product manuals, underwriting guides, training docs, and your own Q&A so your AI keeps getting smarter.",
    action: "Manage Knowledge Base",
    href: "/agent-dashboard",
  },
]

export default function AgentControlCenter() {
  const router = useRouter()

  useEffect(() => {
    if (!window.localStorage.getItem("agent_token")) {
      router.replace("/agent-login")
    }
  }, [router])

  return (
    <main style={{ minHeight: "100vh", background: "#0d0b12", color: "#f7f5fb", fontFamily: "Inter, system-ui, sans-serif" }}>
      <div style={{ maxWidth: 1180, margin: "0 auto", padding: "34px 24px 64px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 18, alignItems: "flex-start", flexWrap: "wrap" }}>
          <div>
            <div style={{ color: "#9d7cff", fontWeight: 800, fontSize: 13, letterSpacing: ".06em" }}>MY GOAA AGENT</div>
            <h1 style={{ fontSize: 34, margin: "10px 0 8px", letterSpacing: "-.035em" }}>Your AI Professional Workspace</h1>
            <p style={{ color: "#aaa4b5", maxWidth: 700, lineHeight: 1.7, margin: 0 }}>
              Let your AI learn your materials and communication style to help you understand customer needs, prepare responses, and route actionable customers to your workspace.
            </p>
          </div>
          <button onClick={() => router.push("/agent-dashboard")} style={{ border: "1px solid #383242", borderRadius: 11, background: "#17141d", color: "#ddd7e7", padding: "10px 14px", cursor: "pointer" }}>Back to Agent Console</button>
        </div>

        <section style={{ marginTop: 30, padding: 22, borderRadius: 18, border: "1px solid #3a3150", background: "linear-gradient(145deg,#211735,#14121b)" }}>
          <div style={{ color: "#a891f2", fontSize: 12, fontWeight: 800 }}>YOUR AI IS THE PRODUCT</div>
          <div style={{ fontSize: 24, fontWeight: 800, marginTop: 9 }}>Better materials make a smarter AI; clearer preferences make answers sound like you.</div>
          <div style={{ color: "#aaa4b5", fontSize: 14, lineHeight: 1.7, marginTop: 8 }}>
            Platform rules guard compliance and facts; your private knowledge adds depth; your preferences shape the voice. Together they create a truly personal My GOAA Agent。
          </div>
        </section>

        <section style={{ marginTop: 20, display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: 14 }}>
          {cards.map((card) => (
            <article key={card.title} style={{ padding: 20, borderRadius: 16, background: "#17151e", border: "1px solid #2c2835", display: "flex", minHeight: 190, flexDirection: "column" }}>
              <h2 style={{ fontSize: 18, margin: 0 }}>{card.title}</h2>
              <p style={{ color: "#9993a4", fontSize: 13, lineHeight: 1.65, flex: 1 }}>{card.copy}</p>
              <button onClick={() => router.push(card.href)} style={{ alignSelf: "flex-start", border: 0, borderRadius: 10, background: "#7655df", color: "white", padding: "9px 13px", fontWeight: 750, cursor: "pointer" }}>{card.action}</button>
            </article>
          ))}
        </section>

        <section style={{ marginTop: 20, padding: 18, borderRadius: 15, border: "1px solid #27232f", background: "#121018", color: "#aaa4b5", fontSize: 13, lineHeight: 1.7 }}>
          <b style={{ color: "#f4f1f8" }}>Current product principle:</b> Agent preferences may change style and retrieval focus, but cannot override platform facts, compliance rules, license boundaries, or create product guarantees.
        </section>
      </div>
    </main>
  )
}
