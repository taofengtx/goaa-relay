"use client"
import { useEffect, useState } from "react"
import { writeSignedInCookieToDocument } from "../../../lib/goaa-cookie"

// Google OAuth callback hop (registered redirect URI):
//   https://planning.goaa.ai/auth/google/callback
//
// Google redirects the browser here with ?code&state. This page exchanges the
// code with the backend (api.goaa.ai /api/v1/auth/google/callback — the same
// registered redirect_uri is used server-side), persists the issued client
// token exactly like a normal email login (localStorage + goaa_signed_in
// mirror cookie), then finalizes through /client-login?google=done so the
// existing return-target logic (pending purchase / prompt / order) is reused.

const OPENCLAW_URL = process.env.NEXT_PUBLIC_OPENCLAW_URL ?? "https://api.goaa.ai"

export default function GoogleCallback() {
  const [state, setState] = useState<"working" | "error" | "done">("working")
  const [message, setMessage] = useState("Completing Google sign-in…")

  useEffect(() => {
    let cancelled = false
    const params = new URLSearchParams(window.location.search)
    const code = params.get("code") || ""
    const stateParam = params.get("state") || ""
    const error = params.get("error") || ""

    async function run() {
      if (error) {
        setState("error")
        setMessage(`Google sign-in could not be completed (${error}). Please try again.`)
        return
      }
      if (!code || !stateParam) {
        setState("error")
        setMessage("Google sign-in is missing required data. Please try again.")
        return
      }
      try {
        const res = await fetch(
          `${OPENCLAW_URL}/api/v1/auth/google/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(stateParam)}`,
          { method: "GET", headers: { Accept: "application/json" } },
        )
        const data = await res.json()
        if (!res.ok || data.status !== "success") {
          setState("error")
          setMessage(data.message || data.detail || "Google sign-in could not be completed. Please try again.")
          return
        }
        localStorage.setItem("client_token", data.token)
        localStorage.setItem("client_username", data.user?.email || "")
        // Mirror flag cookie (flag only; no token). No-op outside goaa.ai.
        writeSignedInCookieToDocument()
        if (cancelled) return
        setState("done")
        setMessage("Signed in with Google. Opening your account…")
        // Reuse the client-login return-target logic.
        window.location.replace("/client-login?google=done")
      } catch {
        if (!cancelled) {
          setState("error")
          setMessage("Sign-in is temporarily unavailable. Please try again shortly.")
        }
      }
    }
    run()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main style={{ minHeight: "100vh", background: "#08080c", color: "#fff", fontFamily: "system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif", display: "grid", placeItems: "center", padding: 24 }}>
      <section style={{ width: "min(100%, 420px)", border: "1px solid rgba(255,255,255,.12)", background: "linear-gradient(180deg,rgba(30,30,38,.98),rgba(18,18,24,.98))", borderRadius: 28, padding: "40px 34px", textAlign: "center", boxShadow: "0 30px 90px rgba(0,0,0,.45)" }}>
        <img src="/goaa-logo.svg" alt="GOAA" width={48} height={48} style={{ display: "block", margin: "0 auto 18px", borderRadius: "50%" }} />
        <p style={{ margin: 0, color: "rgba(255,255,255,.8)", fontSize: 15, lineHeight: 1.6 }}>{message}</p>
        {state === "error" && (
          <p style={{ margin: "22px 0 0" }}>
            <a href="/client-login" style={{ color: "#fff", fontSize: 14 }}>Back to sign in</a>
          </p>
        )}
      </section>
    </main>
  )
}
