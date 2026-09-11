"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"

const OPENCLAW_URL = process.env.NEXT_PUBLIC_OPENCLAW_URL ?? "https://api.goaa.ai"

type Skill = {
  id: string
  name: string
  description: string
  category: string
  price: number
  credits_per_use: number
  developer_name: string
  rating: number
  sales: number
  status: string
}

type Category = { id: string; name: string; icon: string }

const CATEGORY_COLORS: Record<string, string> = {
  video: "#e0e7ff",
  tax: "#fef9c3",
  realestate: "#dcfce7",
  legal: "#fce7f3",
  immigration: "#e0f2fe",
  insurance: "#fff7ed",
}

export default function SkillsMarket() {
  const router = useRouter()
  const [skills, setSkills] = useState<Skill[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [search, setSearch] = useState("")
  const [credits, setCredits] = useState(0)
  const [username, setUsername] = useState("")
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<"market" | "my_skills" | "upload">("market")
  const [mySkills, setMySkills] = useState<Skill[]>([])
  const [totalRevenue, setTotalRevenue] = useState(0)
  const [uploadForm, setUploadForm] = useState({
    name: "", description: "", category: "video",
    price: "", credits_per_use: ""
  })
  const [message, setMessage] = useState("")

  useEffect(() => {
    const token = localStorage.getItem("agent_token")
    const user = localStorage.getItem("agent_username")
    if (!token) { router.push("/agent-login"); return }
    setUsername(user || "")
    fetchSkills()
    fetchCredits(user || "")
    fetchMySkills(user || "")
  }, [])

  async function fetchSkills() {
    setLoading(true)
    try {
      const url = selectedCategory !== "all"
        ? `${OPENCLAW_URL}/api/v1/skills?category=${selectedCategory}`
        : `${OPENCLAW_URL}/api/v1/skills`
      const r = await fetch(url)
      const data = await r.json()
      setSkills(data.skills || [])
      setCategories(data.categories || [])
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  async function fetchCredits(uid: string) {
    try {
      const r = await fetch(`${OPENCLAW_URL}/api/v1/credits/${uid}`)
      const data = await r.json()
      setCredits(data.credits || 0)
    } catch (e) { console.error(e) }
  }

  async function fetchMySkills(uid: string) {
    try {
      const r = await fetch(`${OPENCLAW_URL}/api/v1/skills/developer/${uid}`)
      const data = await r.json()
      setMySkills(data.skills || [])
      setTotalRevenue(data.total_revenue || 0)
    } catch (e) { console.error(e) }
  }

  async function handlePurchase(skillId: string, skillName: string, price: number) {
    try {
      const r = await fetch(`${OPENCLAW_URL}/api/v1/skills/${skillId}/purchase`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: username })
      })
      const data = await r.json()
      setMessage(`✅ Purchased 《${skillName}》 for $${price}`)
      setTimeout(() => setMessage(""), 3000)
    } catch (e) { setMessage("❌ Purchase failed") }
  }

  async function handleTopup() {
    try {
      const r = await fetch(`${OPENCLAW_URL}/api/v1/credits/${username}/topup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan: "starter" })
      })
      const data = await r.json()
      setCredits(data.total)
      setMessage("✅ 1,000 Credits added")
      setTimeout(() => setMessage(""), 3000)
    } catch (e) { setMessage("❌ Top-up failed") }
  }

  async function handleUpload() {
    if (!uploadForm.name || !uploadForm.description || !uploadForm.price) {
      setMessage("❌ Please fill in all required fields"); return
    }
    try {
      const r = await fetch(`${OPENCLAW_URL}/api/v1/skills/upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...uploadForm,
          price: parseFloat(uploadForm.price),
          credits_per_use: parseInt(uploadForm.credits_per_use) || 50,
          developer_id: username,
          developer_name: username
        })
      })
      const data = await r.json()
      setMessage("✅ Skill submitted for review. It will be listed once approved.")
      setUploadForm({ name: "", description: "", category: "video", price: "", credits_per_use: "" })
      fetchMySkills(username)
      setTimeout(() => setMessage(""), 4000)
    } catch (e) { setMessage("❌ Upload failed") }
  }

  const filteredSkills = skills.filter(s =>
    (selectedCategory === "all" || s.category === selectedCategory) &&
    (search === "" || s.name.includes(search) || s.description.includes(search))
  )

  return (
    <div style={{ minHeight: "100vh", background: "#fafaf9", fontFamily: "system-ui,sans-serif" }}>

      {/* Top Navigation */}
      <div style={{
        background: "white", borderBottom: "1px solid #e8e6e0",
        padding: "0 32px", height: 56, display: "flex",
        alignItems: "center", justifyContent: "space-between"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <button onClick={() => router.push("/agent-dashboard")}
            style={{ background: "none", border: "none", cursor: "pointer", color: "#6b7280", fontSize: 14 }}>
            ← Back to Workspace
          </button>
          <span style={{ color: "#e5e7eb" }}>|</span>
          <span style={{ fontWeight: 600, fontSize: 16, color: "#18181b" }}>🛒 Skill Marketplace</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            background: "#fef9c3", border: "1px solid #fde68a",
            borderRadius: 20, padding: "4px 12px", fontSize: 13,
            color: "#92400e", fontWeight: 500
          }}>
            ⚡ {credits} Credits
          </div>
          <button onClick={handleTopup} style={{
            background: "#18181b", color: "white", border: "none",
            borderRadius: 8, padding: "6px 14px", fontSize: 13, cursor: "pointer"
          }}>Top Up</button>
        </div>
      </div>

      {/* Message */}
      {message && (
        <div style={{
          background: message.startsWith("✅") ? "#dcfce7" : "#fee2e2",
          border: `1px solid ${message.startsWith("✅") ? "#86efac" : "#fca5a5"}`,
          padding: "10px 32px", fontSize: 14, textAlign: "center",
          color: message.startsWith("✅") ? "#166534" : "#991b1b"
        }}>{message}</div>
      )}

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "24px 32px" }}>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 4, marginBottom: 24, background: "#f3f4f6", borderRadius: 10, padding: 4, width: "fit-content" }}>
          {[
            { key: "market", label: "🛒 Market" },
            { key: "my_skills", label: "💼 My Skills" },
            { key: "upload", label: "⬆️ Upload Skill" },
          ].map(tab => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key as any)} style={{
              padding: "8px 20px", borderRadius: 8, border: "none", cursor: "pointer",
              background: activeTab === tab.key ? "white" : "transparent",
              color: activeTab === tab.key ? "#18181b" : "#6b7280",
              fontWeight: activeTab === tab.key ? 600 : 400,
              fontSize: 14,
              boxShadow: activeTab === tab.key ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
            }}>{tab.label}</button>
          ))}
        </div>

        {/* Market Tab */}
        {activeTab === "market" && (
          <>
            {/* Search and Category */}
            <div style={{ display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap" }}>
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search skills..."
                style={{
                  flex: 1, minWidth: 200, padding: "10px 16px",
                  border: "1px solid #e5e7eb", borderRadius: 10,
                  fontSize: 14, outline: "none"
                }}
              />
              <button
                onClick={() => setSelectedCategory("all")}
                style={{
                  padding: "10px 16px", borderRadius: 10, border: "1px solid #e5e7eb",
                  background: selectedCategory === "all" ? "#18181b" : "white",
                  color: selectedCategory === "all" ? "white" : "#374151",
                  cursor: "pointer", fontSize: 13
                }}>All</button>
              {categories.map(cat => (
                <button key={cat.id} onClick={() => setSelectedCategory(cat.id)} style={{
                  padding: "10px 16px", borderRadius: 10, border: "1px solid #e5e7eb",
                  background: selectedCategory === cat.id ? "#18181b" : "white",
                  color: selectedCategory === cat.id ? "white" : "#374151",
                  cursor: "pointer", fontSize: 13
                }}>{cat.icon} {cat.name}</button>
              ))}
            </div>

            {/* Skill Card Grid */}
            {loading ? (
              <div style={{ textAlign: "center", padding: 60, color: "#9ca3af" }}>Loading...</div>
            ) : (
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
                gap: 20
              }}>
                {filteredSkills.map(skill => (
                  <div key={skill.id} style={{
                    background: "white", borderRadius: 16,
                    border: "1px solid #e8e6e0", overflow: "hidden",
                    transition: "transform 0.15s, box-shadow 0.15s",
                  }}>
                    {/* Card Accent Bar */}
                    <div style={{
                      height: 6,
                      background: CATEGORY_COLORS[skill.category] || "#f3f4f6"
                    }} />
                    <div style={{ padding: 20 }}>
                      {/* Category Label */}
                      <div style={{ marginBottom: 10 }}>
                        <span style={{
                          background: CATEGORY_COLORS[skill.category] || "#f3f4f6",
                          padding: "3px 10px", borderRadius: 20, fontSize: 11, color: "#374151"
                        }}>
                          {categories.find(c => c.id === skill.category)?.icon} {categories.find(c => c.id === skill.category)?.name || skill.category}
                        </span>
                      </div>

                      <h3 style={{ fontSize: 16, fontWeight: 600, color: "#18181b", margin: "0 0 8px" }}>
                        {skill.name}
                      </h3>
                      <p style={{ fontSize: 13, color: "#6b7280", lineHeight: 1.5, margin: "0 0 16px", height: 60, overflow: "hidden" }}>
                        {skill.description}
                      </p>

                      {/* Stats */}
                      <div style={{ display: "flex", gap: 16, marginBottom: 16, fontSize: 12, color: "#9ca3af" }}>
                        <span>⭐ {skill.rating || "New"}</span>
                        <span>📦 {skill.sales} purchases</span>
                        <span>⚡ {skill.credits_per_use} credits/use</span>
                      </div>

                      {/* Developer */}
                      <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 16 }}>
                        Developer: {skill.developer_name}
                      </div>

                      {/* Buy Button */}
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <span style={{ fontSize: 22, fontWeight: 700, color: "#18181b" }}>${skill.price}</span>
                        <button onClick={() => handlePurchase(skill.id, skill.name, skill.price)} style={{
                          background: "#4f46e5", color: "white", border: "none",
                          borderRadius: 8, padding: "8px 16px", fontSize: 13,
                          cursor: "pointer", fontWeight: 500
                        }}>Buy Now</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {/* My Skills Tab */}
        {activeTab === "my_skills" && (
          <div>
            <div style={{
              background: "white", borderRadius: 16, border: "1px solid #e8e6e0",
              padding: 24, marginBottom: 24,
              display: "flex", gap: 40
            }}>
              <div>
                <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 4 }}>My Skills</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#18181b" }}>{mySkills.length}</div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 4 }}>Total Revenue</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#059669" }}>${totalRevenue.toFixed(2)}</div>
              </div>
              <div>
                <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 4 }}>Platform Share</div>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#4f46e5" }}>50%</div>
              </div>
            </div>

            {mySkills.length === 0 ? (
              <div style={{ textAlign: "center", padding: 60, color: "#9ca3af" }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>📦</div>
                <div>No skills uploaded yet</div>
                <button onClick={() => setActiveTab("upload")} style={{
                  marginTop: 16, background: "#4f46e5", color: "white",
                  border: "none", borderRadius: 8, padding: "10px 20px",
                  cursor: "pointer", fontSize: 14
                }}>Upload Your First Skill</button>
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
                {mySkills.map(skill => (
                  <div key={skill.id} style={{
                    background: "white", borderRadius: 16,
                    border: "1px solid #e8e6e0", padding: 20
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                      <h3 style={{ fontSize: 15, fontWeight: 600, margin: 0 }}>{skill.name}</h3>
                      <span style={{
                        background: skill.status === "active" ? "#dcfce7" : "#fef9c3",
                        color: skill.status === "active" ? "#166534" : "#92400e",
                        padding: "2px 8px", borderRadius: 20, fontSize: 11
                      }}>{skill.status === "active" ? "Listed" : "In Review"}</span>
                    </div>
                    <div style={{ fontSize: 13, color: "#6b7280", marginBottom: 12 }}>{skill.description}</div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                      <span>Price: <strong>${skill.price}</strong></span>
                      <span>Earnings: <strong style={{ color: "#059669" }}>${(skill.sales * skill.price * 0.5).toFixed(2)}</strong></span>
                    </div>
                    <div style={{ fontSize: 12, color: "#9ca3af", marginTop: 8 }}>Sales: {skill.sales}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Upload Skill Tab */}
        {activeTab === "upload" && (
          <div style={{ maxWidth: 600 }}>
            <div style={{
              background: "#ede9fe", borderRadius: 12, padding: "16px 20px",
              marginBottom: 24, fontSize: 14, color: "#4f46e5"
            }}>
              💡 After listing, each sale splits 50/50 with the platform. Usage is billed in Credits.
            </div>

            <div style={{ background: "white", borderRadius: 16, border: "1px solid #e8e6e0", padding: 32 }}>
              <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 24, color: "#18181b" }}>Upload New Skill</h2>

              {[
                { label: "Skill Name *", key: "name", placeholder: "e.g., auto-generate weekly report video" },
                { label: "Description *", key: "description", placeholder: "Describe what the skill does and when to use it..." },
              ].map(field => (
                <div key={field.key} style={{ marginBottom: 16 }}>
                  <label style={{ display: "block", fontSize: 13, color: "#374151", marginBottom: 6, fontWeight: 500 }}>
                    {field.label}
                  </label>
                  {field.key === "description" ? (
                    <textarea
                      value={(uploadForm as any)[field.key]}
                      onChange={e => setUploadForm(prev => ({ ...prev, [field.key]: e.target.value }))}
                      placeholder={field.placeholder}
                      rows={3}
                      style={{
                        width: "100%", padding: "10px 14px", border: "1px solid #e5e7eb",
                        borderRadius: 8, fontSize: 14, outline: "none", resize: "vertical",
                        boxSizing: "border-box"
                      }}
                    />
                  ) : (
                    <input
                      value={(uploadForm as any)[field.key]}
                      onChange={e => setUploadForm(prev => ({ ...prev, [field.key]: e.target.value }))}
                      placeholder={field.placeholder}
                      style={{
                        width: "100%", padding: "10px 14px", border: "1px solid #e5e7eb",
                        borderRadius: 8, fontSize: 14, outline: "none", boxSizing: "border-box"
                      }}
                    />
                  )}
                </div>
              ))}

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: "block", fontSize: 13, color: "#374151", marginBottom: 6, fontWeight: 500 }}>Category</label>
                <select
                  value={uploadForm.category}
                  onChange={e => setUploadForm(prev => ({ ...prev, category: e.target.value }))}
                  style={{
                    width: "100%", padding: "10px 14px", border: "1px solid #e5e7eb",
                    borderRadius: 8, fontSize: 14, outline: "none", background: "white"
                  }}
                >
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>
                  ))}
                </select>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
                <div>
                  <label style={{ display: "block", fontSize: 13, color: "#374151", marginBottom: 6, fontWeight: 500 }}>
                    Price (USD) *
                  </label>
                  <input
                    value={uploadForm.price} type="number"
                    onChange={e => setUploadForm(prev => ({ ...prev, price: e.target.value }))}
                    placeholder="100"
                    style={{
                      width: "100%", padding: "10px 14px", border: "1px solid #e5e7eb",
                      borderRadius: 8, fontSize: 14, outline: "none", boxSizing: "border-box"
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 13, color: "#374151", marginBottom: 6, fontWeight: 500 }}>
                    Credits per Use
                  </label>
                  <input
                    value={uploadForm.credits_per_use} type="number"
                    onChange={e => setUploadForm(prev => ({ ...prev, credits_per_use: e.target.value }))}
                    placeholder="50"
                    style={{
                      width: "100%", padding: "10px 14px", border: "1px solid #e5e7eb",
                      borderRadius: 8, fontSize: 14, outline: "none", boxSizing: "border-box"
                    }}
                  />
                </div>
              </div>

              <button onClick={handleUpload} style={{
                width: "100%", background: "#4f46e5", color: "white",
                border: "none", borderRadius: 10, padding: "14px",
                fontSize: 15, fontWeight: 600, cursor: "pointer"
              }}>Submit for Review</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
