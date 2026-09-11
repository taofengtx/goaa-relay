"use client"
import { useState } from "react"

const API_BASE = process.env.NEXT_PUBLIC_OPENCLAW_URL ?? "https://api.goaa.ai"
const AGENT_RETURN_KEY = "goaa_agent_return_v1"

function resumeTarget(): string | null {
  if (typeof window === "undefined") return null
  const params = new URLSearchParams(window.location.search)
  // /agent-login?resume=1&reason=order&order=<id> → resume the same order
  if (params.get("resume") === "1" && params.get("reason") === "order") {
    const orderId = params.get("order")
    if (orderId) return `/agent-order-live?order=${encodeURIComponent(orderId)}`
  }
  const saved = window.localStorage.getItem(AGENT_RETURN_KEY)
  if (saved && saved.startsWith("/agent-order-live")) {
    window.localStorage.removeItem(AGENT_RETURN_KEY)
    return saved
  }
  return null
}

export default function AgentLogin() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [status, setStatus] = useState("")
  const [loading, setLoading] = useState(false)
  const resume = resumeTarget()

  async function handleLogin() {
    if (loading || !username || !password) return
    setLoading(true)
    setStatus("Verifying...")
    try {
      const res = await fetch(`${API_BASE}/api/v1/agent/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      })
      const data = await res.json().catch(() => ({}))

      if (res.ok && data.status === "success" && data.token) {
        localStorage.setItem("agent_token", data.token)
        localStorage.setItem("agent_username", data.username || username)
        if (data.agent_id) localStorage.setItem("agent_id", data.agent_id)

        setTimeout(() => {
          // Agent Auth Bridge: resume the order we came from, never the homepage.
          const target = resumeTarget()
          window.location.href = target || "/agent-dashboard"
        }, 500)
      } else {
        setStatus("❌ We couldn\u0027t sign you in. Please check your credentials and try again.")
      }
    } catch (e: any) {
      setStatus("❌ Sign-in is temporarily unavailable. Please try again shortly.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%)",
      fontFamily: "system-ui, -apple-system, sans-serif",
      padding: 20,
      boxSizing: "border-box",
    }}>
      <div style={{
        background: "#1a1a2e",
        padding: 48,
        borderRadius: 16,
        width: "100%",
        maxWidth: 420,
        border: "1px solid #333",
        boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
      }}>
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ color: "#fff", marginBottom: 8, fontSize: 28, fontWeight: 700 }}>goaa.ai</h1>
          <p style={{ color: "#888", marginBottom: 4, fontSize: 14 }}>Agent Workspace Sign-In</p>
          <p style={{ color: "#4f46e5", marginBottom: 0, fontSize: 11, letterSpacing: "0.5px" }}>My GOAA Agent · Professional Console</p>
        </div>

        <input
          type="text"
          autoComplete="username"
          placeholder="Username / Email"
          value={username}
          onChange={e => setUsername(e.target.value)}
          onKeyDown={e => e.key === "Enter" && void handleLogin()}
          disabled={loading}
          style={{ width: "100%", padding: "14px", marginBottom: 12, background: "#2a2a3e", border: "1px solid #444", borderRadius: 8, color: "#fff", fontSize: 14, boxSizing: "border-box", opacity: loading ? 0.6 : 1, transition: "all 0.2s" }}
        />

        <input
          type="password"
          autoComplete="current-password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          onKeyDown={e => e.key === "Enter" && void handleLogin()}
          disabled={loading}
          style={{ width: "100%", padding: "14px", marginBottom: 24, background: "#2a2a3e", border: "1px solid #444", borderRadius: 8, color: "#fff", fontSize: 14, boxSizing: "border-box", opacity: loading ? 0.6 : 1, transition: "all 0.2s" }}
        />

        <button
          onClick={() => void handleLogin()}
          disabled={loading || !username || !password}
          style={{ width: "100%", padding: "14px", background: loading ? "#555" : (!username || !password ? "#666" : "#4F46E5"), color: "#fff", border: "none", borderRadius: 8, fontSize: 16, fontWeight: 600, cursor: loading ? "wait" : (!username || !password ? "not-allowed" : "pointer"), transition: "all 0.2s", opacity: !username || !password ? 0.5 : 1 }}
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>

        {status && (
          <p style={{ marginTop: 20, color: status.includes("✅") ? "#4ade80" : status.includes("Verifying") ? "#c4b5fd" : "#ef4444", fontSize: 13, textAlign: "center", minHeight: "20px" }}>{status}</p>
        )}

        <hr style={{ margin: "24px 0", border: "none", borderTop: "1px solid #333" }} />
        <p style={{ color: "#666", fontSize: 12, textAlign: "center", margin: 0 }}>🔐 Secure access for GOAA professionals</p>
      </div>
    </div>
  )
}
