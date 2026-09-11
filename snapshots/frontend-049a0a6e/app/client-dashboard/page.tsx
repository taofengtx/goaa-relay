"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"

const OPENCLAW_URL = process.env.NEXT_PUBLIC_OPENCLAW_URL ?? "https://api.goaa.ai"

async function chat(userId: string, content: string): Promise<string> {
  const r1 = await fetch(OPENCLAW_URL + "/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, content: "__init__" }),
  })
  if (!r1.ok) throw new Error(`Session failed: ${r1.status}`)
  const d1 = await r1.json()
  const wsUrl = d1.data?.ws_url || d1.ws_url
  if (!wsUrl) throw new Error("No WebSocket URL")
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl)
    const t = setTimeout(() => { ws.close(); reject(new Error("Timeout")) }, 60000)
    ws.onopen = () => ws.send(JSON.stringify({ content, role: "user" }))
    ws.onmessage = (e) => {
      clearTimeout(t); ws.close()
      try { const d = JSON.parse(e.data); resolve(d.response || d.data?.response || e.data) }
      catch { resolve(e.data) }
    }
    ws.onerror = () => { clearTimeout(t); reject(new Error("WebSocket error")) }
  })
}

type Task = { id: number; title: string; status: "done" | "pending" | "running" }

const NAV_ITEMS = [
  { icon: "⊕", label: "My Plans", active: true },
  { icon: "◈", label: "Professionals", active: false },
  { icon: "⌕", label: "Search", active: false },
  { icon: "▤", label: "Library", active: false },
]

export default function Dashboard() {
  const router = useRouter()
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [username, setUsername] = useState("")
  const [response, setResponse] = useState("")
  const [tasks, setTasks] = useState<Task[]>([
    { id: 1, title: "My Insurance Plan", status: "done" },
    { id: 2, title: "Asset Allocation Report", status: "done" },
    { id: 3, title: "Immigration Plan", status: "done" },
  ])
  const [activeTask, setActiveTask] = useState<number | null>(null)

  useEffect(() => {
    const token = localStorage.getItem("client_token")
    const user = localStorage.getItem("client_username")
    if (!token) { router.push("/client-login"); return }
    setUsername(user || "Customer")
  }, [router])

  async function handleSubmit() {
    if (!input.trim() || loading) return
    setLoading(true)
    const msg = input
    setInput("")
    setResponse("")
    const newId = Date.now()
    const newTask: Task = { id: newId, title: msg, status: "running" }
    setTasks(prev => [newTask, ...prev])
    setActiveTask(newId)
    try {
      const userId = localStorage.getItem("client_username") || "agent"
      const result = await chat(userId, msg)
      setResponse(String(result))
      setTasks(prev => prev.map(t => t.id === newId ? { ...t, status: "done" } : t))
    } catch (e: any) {
      setResponse("Error: " + e.message)
      setTasks(prev => prev.map(t => t.id === newId ? { ...t, status: "done" } : t))
    } finally {
      setLoading(false)
    }
  }

  function handleLogout() {
    localStorage.clear()
    router.push("/client-login")
  }

  const statusDot = (status: Task["status"]) => ({
    done: "#34d399",
    pending: "#fbbf24",
    running: "#60a5fa",
  }[status])

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "'SF Pro Display', system-ui, sans-serif", background: "#fafaf9" }}>

      {/* Sidebar */}
      <aside style={{
        width: 260, background: "#f5f4f0", borderRight: "1px solid #e8e6e0",
        display: "flex", flexDirection: "column", flexShrink: 0,
      }}>
        {/* Logo */}
        <div style={{ padding: "18px 16px 14px", borderBottom: "1px solid #e8e6e0", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{display:"flex", alignItems:"center", gap:8}}>
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <circle cx="16" cy="16" r="16" fill="#1a1a1a"/>
              <ellipse cx="16" cy="19" rx="8" ry="6" fill="#e53e3e"/>
              <ellipse cx="16" cy="17" rx="6" ry="5" fill="#fc4e4e"/>
              <circle cx="13" cy="15" r="1.5" fill="#1a1a1a"/>
              <circle cx="19" cy="15" r="1.5" fill="#1a1a1a"/>
              <circle cx="13.5" cy="14.5" r="0.5" fill="white"/>
              <circle cx="19.5" cy="14.5" r="0.5" fill="white"/>
              <path d="M13 18 Q16 20 19 18" stroke="#1a1a1a" strokeWidth="1" fill="none" strokeLinecap="round"/>
              <line x1="12" y1="11" x2="10" y2="8" stroke="#e53e3e" strokeWidth="1.5" strokeLinecap="round"/>
              <line x1="20" y1="11" x2="22" y2="8" stroke="#e53e3e" strokeWidth="1.5" strokeLinecap="round"/>
              <circle cx="22" cy="12" r="3" fill="#4299e1" opacity="0.8"/>
              <circle cx="22" cy="12" r="1.5" fill="#63b3ed"/>
              <text x="16" y="26" textAnchor="middle" fill="white" fontSize="5" fontWeight="bold" fontFamily="sans-serif">GA</text>
            </svg>
            <div>
              <div style={{fontWeight:700, fontSize:14, color:"#18181b", letterSpacing:"-0.3px"}}>goaa.ai</div>
              <div style={{fontSize:10, color:"#9ca3af", marginTop:1}}>Personal Service Center</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ padding: "10px 8px 4px" }}>
          {NAV_ITEMS.map(item => (
            <button key={item.label} style={{
              width: "100%", display: "flex", alignItems: "center", gap: 10,
              padding: "7px 10px", borderRadius: 7, border: "none", cursor: "pointer",
              background: item.active ? "#ebe8ff" : "transparent",
              color: item.active ? "#4f46e5" : "#6b7280",
              fontSize: 13, fontWeight: item.active ? 500 : 400,
              marginBottom: 2, textAlign: "left",
            }}>
              <span style={{ fontSize: 14, opacity: 0.8 }}>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        {/* Tasks */}
        <div style={{ flex: 1, overflowY: "auto", padding: "8px 8px 0" }}>
          <div style={{
            fontSize: 10, color: "#9ca3af", padding: "6px 10px 6px",
            textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 500,
            display: "flex", alignItems: "center", justifyContent: "space-between",
          }}>
            <span>All Tasks</span>
            <span style={{ background: "#e5e7eb", color: "#6b7280", padding: "1px 6px", borderRadius: 10, fontSize: 10 }}>
              {tasks.length}
            </span>
          </div>
          {tasks.map(task => (
            <button key={task.id} onClick={() => setActiveTask(task.id)} style={{
              width: "100%", display: "flex", alignItems: "center", gap: 8,
              padding: "7px 10px", borderRadius: 7, border: "none", cursor: "pointer",
              background: activeTask === task.id ? "#fff" : "transparent",
              boxShadow: activeTask === task.id ? "0 1px 3px rgba(0,0,0,0.06)" : "none",
              marginBottom: 1, textAlign: "left",
            }}>
              <div style={{
                width: 7, height: 7, borderRadius: "50%",
                background: statusDot(task.status), flexShrink: 0,
                boxShadow: task.status === "running" ? "0 0 0 3px rgba(96,165,250,0.2)" : "none",
              }} />
              <span style={{
                fontSize: 12.5, color: "#374151",
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1,
              }}>{task.title}</span>
            </button>
          ))}
        </div>

        {/* User */}
        <div style={{ padding: "10px 8px", borderTop: "1px solid #e8e6e0" }}>
          <button onClick={handleLogout} style={{
            width: "100%", display: "flex", alignItems: "center", gap: 9,
            padding: "8px 10px", background: "none", border: "none",
            borderRadius: 8, cursor: "pointer", color: "#6b7280",
          }}>
            <div style={{
              width: 26, height: 26, background: "#e0e7ff", borderRadius: "50%",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 11, color: "#4f46e5", fontWeight: 600, flexShrink: 0,
            }}>{username[0]?.toUpperCase()}</div>
            <span style={{ fontSize: 12.5, flex: 1, textAlign: "left", color: "#374151" }}>{username}</span>
            <span style={{ fontSize: 11, color: "#9ca3af" }}>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

        {/* Topbar */}
        <div style={{
          height: 46, borderBottom: "1px solid #e8e6e0", background: "#fafaf9",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "0 28px", flexShrink: 0,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 13, color: "#6b7280" }}>goaa.ai Customer Center</span>
            <span style={{
              fontSize: 10, background: "#f3f4f6", color: "#9ca3af",
              padding: "2px 8px", borderRadius: 20, letterSpacing: "0.03em",
            }}>Beta</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {loading && (
              <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#60a5fa", fontSize: 12 }}>
                <div style={{
                  width: 6, height: 6, borderRadius: "50%", background: "#60a5fa",
                  animation: "pulse 1s infinite",
                }} />
                AI thinking
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        <div style={{
          flex: 1, display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center", padding: "32px 40px",
          overflowY: "auto",
        }}>

          {/* Response */}
          {response && (
            <div style={{
              width: "100%", maxWidth: 660, marginBottom: 28,
              background: "white", borderRadius: 14, border: "1px solid #e8e6e0",
              padding: "20px 24px", fontSize: 14, lineHeight: 1.75, color: "#374151",
              whiteSpace: "pre-wrap", boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <div style={{
                  width: 22, height: 22, background: "#18181b", borderRadius: 6,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "white", fontSize: 10, fontWeight: 700,
                }}>G</div>
                <span style={{ fontSize: 12, color: "#9ca3af" }}>AiKa</span>
              </div>
              {response}
            </div>
          )}

          {!response && (
            <div style={{ textAlign: "center", marginBottom: 44 }}>
              <h1 style={{
                fontSize: 30, fontWeight: 600, color: "#18181b",
                letterSpacing: "-0.8px", marginBottom: 10, lineHeight: 1.2,
              }}>Built for life, designed for the future</h1>
              <p style={{ fontSize: 13, color: "#9ca3af", lineHeight: 1.6 }}>
                GOAA AI can help you organize your goals, explore your options, and connect with a professional when you&apos;re ready.
              </p>
            </div>
          )}

          {/* Input */}
          <div style={{
            width: "100%", maxWidth: 660,
            background: "white", border: "1px solid #e0dedd",
            borderRadius: 16, padding: "14px 16px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
            transition: "border-color 0.15s, box-shadow 0.15s",
          }}>
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit() } }}
              placeholder="What would you like help with today?"
              rows={1}
              style={{
                width: "100%", border: "none", outline: "none", resize: "none",
                fontSize: 14, color: "#18181b", lineHeight: 1.6,
                minHeight: 22, maxHeight: 160, fontFamily: "inherit",
                background: "transparent",
              }}
            />
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 10 }}>
              <span style={{ fontSize: 11, color: "#c4c0ba" }}>Enter to send · Shift+Enter for a new line</span>
              <button
                onClick={handleSubmit}
                disabled={loading || !input.trim()}
                style={{
                  width: 32, height: 32, borderRadius: 9, border: "none", cursor: loading || !input.trim() ? "default" : "pointer",
                  background: loading || !input.trim() ? "#f3f4f6" : "#18181b",
                  color: loading || !input.trim() ? "#9ca3af" : "white",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 15, transition: "background 0.15s",
                  flexShrink: 0,
                }}
              >
                {loading ? "·" : "↑"}
              </button>
            </div>
          </div>

          {/* Quick actions */}
          {!response && (
            <div style={{ display: "flex", gap: 8, marginTop: 20, flexWrap: "wrap", justifyContent: "center" }}>
              {["Tax & Finance", "Insurance Analysis", "Property Investment", "Education Consulting", "Immigration", "Trust Planning"].map(q => (
                <button key={q} onClick={() => setInput(q)} style={{
                  padding: "6px 14px", background: "white", border: "1px solid #e8e6e0",
                  borderRadius: 20, fontSize: 12, color: "#6b7280", cursor: "pointer",
                  transition: "border-color 0.15s",
                }}>{q}</button>
              ))}
            </div>
          )}
        </div>
      </main>

      <style>{`
        @keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.4 } }
        textarea::placeholder { color: #c4c0ba; }
        button:hover { opacity: 0.9; }
      `}</style>
    </div>
  )
}

