"use client"
import { FormEvent, useEffect, useRef, useState } from "react"
import { writeSignedInCookieToDocument } from "../lib/goaa-cookie"
import { resolveVisitorDestination } from "../lib/client-login-dismiss"

const AUTH_RETURN_KEY = "goaa_auth_return_v1"
const PENDING_PROMPT_KEY = "goaa_pending_prompt_v1"
const PENDING_PURCHASE_KEY = "goaa_pending_purchase_v1"

// NEXT_PUBLIC_* vars are inlined at build time; fall back to the public
// canonical endpoint so a preview build without the env var can log in.
// NOTE: ?? (not ||) keeps an explicit empty build-time value (same-origin
// proxy mode) intact; the other consumers already use ??.
const OPENCLAW_URL = process.env.NEXT_PUBLIC_OPENCLAW_URL ?? "https://api.goaa.ai"

type AuthCaps = { google: boolean; emailCode: boolean }
type RegisterStep = "form" | "code"

const buttonStyle = {
  width: "100%",
  minHeight: 52,
  borderRadius: 999,
  border: "1px solid rgba(255,255,255,.28)",
  background: "rgba(255,255,255,.035)",
  color: "#fff",
  fontSize: 15,
  fontWeight: 600,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 12,
  cursor: "pointer",
} as const

const inputStyle = {
  width: "100%",
  boxSizing: "border-box" as const,
  minHeight: 54,
  borderRadius: 15,
  border: "1px solid rgba(255,255,255,.16)",
  background: "rgba(255,255,255,.055)",
  color: "#fff",
  padding: "0 16px",
  fontSize: 15,
  outline: "none",
} as const

const passwordInputStyle = {
  ...inputStyle,
  paddingRight: 48,
} as const

// Eye toggle that reveals/hides a password field. A real <button type="button">
// so it is Tab-focusable and Enter/Space activate it natively; the parent
// <input type> switch is the only thing it touches (no submit/validation
// changes). Label flips with state, aria-pressed mirrors the visible state.
const passwordRevealBtnStyle = {
  position: "absolute",
  top: "50%",
  right: 6,
  transform: "translateY(-50%)",
  width: 40,
  height: 40,
  borderRadius: 12,
  border: 0,
  background: "transparent",
  color: "rgba(255,255,255,.6)",
  cursor: "pointer",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 0,
} as const

function PasswordRevealButton({ visible, onToggle }: { visible: boolean; onToggle: () => void }) {
  const label = visible ? "Hide password" : "Show password"
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={label}
      aria-pressed={visible}
      title={label}
      style={passwordRevealBtnStyle}
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        focusable="false"
      >
        <path d="M1.8 12S5.6 4.9 12 4.9 22.2 12 22.2 12 18.4 19.1 12 19.1 1.8 12 1.8 12Z" />
        {visible ? (
          <path d="M4.2 4.2l15.6 15.6" />
        ) : (
          <circle cx="12" cy="12" r="3.1" />
        )}
      </svg>
    </button>
  )
}

const labelStyle = {
  display: "block",
  margin: "16px 0 6px",
  color: "rgba(255,255,255,.55)",
  fontSize: 12,
  fontWeight: 600,
  letterSpacing: ".02em",
} as const

export default function ClientLogin() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  // Independent reveal toggles (type password<->text). Default hidden.
  const [loginPwVisible, setLoginPwVisible] = useState(false)
  const [regPwVisible, setRegPwVisible] = useState(false)
  const [regPw2Visible, setRegPw2Visible] = useState(false)
  const [status, setStatus] = useState("")
  const [loading, setLoading] = useState(false)
  const [hasSavedPrompt, setHasSavedPrompt] = useState(false)
  const [hasPendingPurchase, setHasPendingPurchase] = useState(false)

  // Feature gates: backend /api/v1/auth/status. On failure (pre-deploy /
  // unreachable) we fail closed: Google + email registration hidden, classic
  // email login and Continue as guest always remain.
  const [caps, setCaps] = useState<AuthCaps | null>(null)
  const [mode, setMode] = useState<"login" | "register">("login")

  // Registration state (email-code flow)
  const [regEmail, setRegEmail] = useState("")
  const [regCode, setRegCode] = useState("")
  const [regPassword, setRegPassword] = useState("")
  const [regPassword2, setRegPassword2] = useState("")
  const [regStep, setRegStep] = useState<RegisterStep>("form")
  const [regStatus, setRegStatus] = useState("")
  const [regLoading, setRegLoading] = useState(false)
  const [resendAfter, setResendAfter] = useState(0)
  const [justSignedInViaGoogle, setJustSignedInViaGoogle] = useState(false)

  const emailRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)
  const emailStateRef = useRef(email)
  const passwordStateRef = useRef(password)
  emailStateRef.current = email
  passwordStateRef.current = password

  useEffect(() => {
    setHasSavedPrompt(Boolean(window.localStorage.getItem(PENDING_PROMPT_KEY)))
    setHasPendingPurchase(Boolean(window.localStorage.getItem(PENDING_PURCHASE_KEY)))
    // Success hop from /auth/google/callback: token already stored -> finalize.
    const params = new URLSearchParams(window.location.search)
    if (params.get("google") === "done" && window.localStorage.getItem("client_token")) {
      setJustSignedInViaGoogle(true)
      setStatus("Signed in with Google. Opening your account…")
      window.setTimeout(returnAfterLogin, 500)
    }
    // Auth capability probe (fail closed -> both hidden when unavailable).
    if (typeof fetch !== "function") {
      setCaps({ google: false, emailCode: false })
    } else {
      fetch(`${OPENCLAW_URL}/api/v1/auth/status`, { method: "GET" })
        .then((r) => (r.ok ? r.json() : null))
        .then((d) => setCaps({ google: Boolean(d?.google), emailCode: Boolean(d?.email_code) }))
        .catch(() => setCaps({ google: false, emailCode: false }))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Resend countdown
  useEffect(() => {
    if (resendAfter <= 0) return
    const t = window.setInterval(() => setResendAfter((s) => Math.max(0, s - 1)), 1000)
    return () => window.clearInterval(t)
  }, [resendAfter > 0])

  // Chrome autofill sometimes fills controlled inputs without firing onChange,
  // which leaves React state empty and the submit button permanently disabled
  // even though the fields look filled. Poll the DOM values and mirror them
  // into state so the button reflects what the user actually sees.
  useEffect(() => {
    const timer = window.setInterval(() => {
      const e = emailRef.current
      const p = passwordRef.current
      if (e && e.value !== emailStateRef.current) setEmail(e.value)
      if (p && p.value !== passwordStateRef.current) setPassword(p.value)
    }, 250)
    return () => window.clearInterval(timer)
  }, [])

  // Esc behaves exactly like the close (X) button: continue as a guest.
  // No side effects other than the same allowlisted redirect.
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") goAsGuest()
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [])

  function socialUnavailable(provider: string) {
    const messages: Record<string, string> = {
      Google: "Google sign-in is coming soon. Please continue with email for now.",
      Apple: "Apple sign-in is coming soon. Please continue with email for now.",
      phone: "Phone sign-in is coming soon. Please continue with email for now.",
    }
    setStatus(messages[provider] || "This sign-in option is coming soon. Please continue with email for now.")
  }

  function startGoogleSignIn() {
    if (!caps?.google) {
      socialUnavailable("Google")
      return
    }
    // Browser-level redirect to backend /auth/google/authorize -> Google
    // consent screen -> callback on /auth/google/callback (registered URI).
    window.location.assign(`${OPENCLAW_URL}/api/v1/auth/google/authorize`)
  }

  // Visitor dismiss: close the sign-in card and keep using the customer area
  // WITHOUT authenticating. Pure redirect — no login state, no goaa_signed_in
  // cookie, no storage writes/removals, no business API calls. The return
  // target must pass the same-origin allowlist in lib/client-login-dismiss
  // (mirrors the anti-open-redirect rule of /client-logout); anything else
  // falls back to /planning. resume/reason/order params attached to the
  // return URL survive untouched so the existing sign-in-prompt flow on the
  // planning side behaves exactly as before.
  function goAsGuest() {
    const params = new URLSearchParams(window.location.search)
    const baseOrigin = window.location.origin
    const destination = resolveVisitorDestination(params.get("return"), baseOrigin)
    window.location.assign(destination)
  }

  function returnAfterLogin() {
    const purchaseTarget = window.localStorage.getItem(PENDING_PURCHASE_KEY)
    if (purchaseTarget) {
      window.localStorage.removeItem(PENDING_PURCHASE_KEY)
      window.localStorage.removeItem(AUTH_RETURN_KEY)
      window.location.href = purchaseTarget
      return
    }

    const params = new URLSearchParams(window.location.search)

    // Direct order-login entry: /client-login?order=<id> should always resume
    // the same customer order after successful authentication.
    const orderId = params.get("order")
    if (orderId) {
      window.localStorage.removeItem(AUTH_RETURN_KEY)
      window.localStorage.setItem("goaa_active_order_id", orderId)
      window.location.href = `/customer-order-live?order=${encodeURIComponent(orderId)}`
      return
    }

    // URL fallback: arriving from /connect-pass with ?resume=1&reason=purchase
    // but no saved pending-purchase key must resume the purchase flow, never
    // bounce to the homepage.
    if (params.get("resume") === "1" && params.get("reason") === "purchase") {
      window.localStorage.removeItem(AUTH_RETURN_KEY)
      window.location.href = "/connect-pass?source=planning"
      return
    }

    // If another protected page explicitly saved a return target, honor it.
    // Otherwise a normal customer login should land in the service-order area,
    // not back on the marketing homepage.
    const target = window.localStorage.getItem(AUTH_RETURN_KEY) || "/client-dashboard/orders"
    window.localStorage.removeItem(AUTH_RETURN_KEY)
    window.location.href = target
  }

  function persistAuthSession(token: string, username: string) {
    localStorage.setItem("client_token", token)
    localStorage.setItem("client_username", username)
    // Mirror the signed-in flag to the .goaa.ai cookie space (flag only,
    // never the token/username). No-op outside goaa.ai hosts.
    writeSignedInCookieToDocument()
  }

  async function handleLogin(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault()
    // Read the real DOM values as a fallback: autofill / password managers can
    // fill fields without React state being updated yet.
    const form = event?.currentTarget
    const formEmail = (form?.elements.namedItem("email") as HTMLInputElement | null)?.value ?? ""
    const formPassword = (form?.elements.namedItem("password") as HTMLInputElement | null)?.value ?? ""
    const finalEmail = formEmail.trim() || email.trim()
    const finalPassword = formPassword || password

    if (!finalEmail) return
    if (!showPassword) {
      setShowPassword(true)
      setStatus("")
      return
    }
    if (!finalPassword) return

    setLoading(true)
    setStatus("Verifying...")
    try {
      const res = await fetch(`${OPENCLAW_URL}/api/v1/client/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: finalEmail, password: finalPassword }),
      })
      const data = await res.json()

      if (res.ok && data.status === "success") {
        persistAuthSession(data.token, data.username || finalEmail)
        setStatus(hasPendingPurchase ? "Signed in. Resuming pass purchase…" : hasSavedPrompt ? "Signed in. Resuming your topic…" : "Signed in. Opening your service order…")
        window.setTimeout(returnAfterLogin, 450)
      } else {
        setStatus("We couldn\u0027t sign you in. Please check your credentials and try again.")
      }
    } catch (error: any) {
      setStatus("Sign-in is temporarily unavailable. Please try again shortly.")
    } finally {
      setLoading(false)
    }
  }

  // ── Email-code registration ─────────────────────────────────
  async function handleSendCode(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault()
    const finalEmail = regEmail.trim()
    if (!finalEmail) return
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(finalEmail)) {
      setRegStatus("Please enter a valid email address.")
      return
    }
    setRegLoading(true)
    setRegStatus("Sending verification code…")
    try {
      const res = await fetch(`${OPENCLAW_URL}/api/v1/auth/email-code/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: finalEmail }),
      })
      const data = await res.json()
      if (res.ok && data.status === "success") {
        setRegStep("code")
        setResendAfter(60)
        setRegStatus(`Verification code sent to ${finalEmail}. It expires in 10 minutes.`)
      } else if (res.status === 409) {
        setRegStatus(data.message || "An account with this email already exists. Sign in instead.")
        // flip back to the login card and prefill the email
        setEmail(finalEmail)
        setMode("login")
      } else {
        setRegStatus(data.message || "We couldn\u0027t send the code. Please try again.")
      }
    } catch (error: any) {
      setRegStatus("Email service is temporarily unavailable. Please try again shortly.")
    } finally {
      setRegLoading(false)
    }
  }

  async function handleRegister(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault()
    const finalCode = regCode.trim()
    if (!/^\d{6}$/.test(finalCode)) {
      setRegStatus("Please enter the 6-digit code from the email.")
      return
    }
    if (regPassword.length < 8) {
      setRegStatus("Password must be at least 8 characters.")
      return
    }
    if (regPassword !== regPassword2) {
      setRegStatus("Passwords do not match.")
      return
    }
    setRegLoading(true)
    setRegStatus("Creating your account…")
    try {
      const res = await fetch(`${OPENCLAW_URL}/api/v1/auth/email-code/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: regEmail.trim(), code: finalCode, password: regPassword }),
      })
      const data = await res.json()
      if (res.ok && data.status === "success") {
        persistAuthSession(data.token, data.user?.email || regEmail.trim())
        setStatus("Account created. You\u0027re signed in. Opening your account…")
        window.setTimeout(returnAfterLogin, 450)
      } else {
        setRegStatus(data.message || "We couldn\u0027t create your account. Please try again.")
      }
    } catch (error: any) {
      setRegStatus("Registration is temporarily unavailable. Please try again shortly.")
    } finally {
      setRegLoading(false)
    }
  }

  return (
    <main style={{ minHeight: "100vh", background: "#08080c", color: "#fff", fontFamily: "system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif", display: "grid", placeItems: "center", padding: 24 }}>
      <section style={{ position: "relative", width: "min(100%, 470px)", border: "1px solid rgba(255,255,255,.12)", background: "linear-gradient(180deg,rgba(30,30,38,.98),rgba(18,18,24,.98))", borderRadius: 28, padding: "34px 34px 30px", boxShadow: "0 30px 90px rgba(0,0,0,.45)" }}>
        <button
          type="button"
          onClick={goAsGuest}
          aria-label="Continue as guest"
          title="Continue as guest"
          style={{ position: "absolute", top: 16, right: 16, width: 38, height: 38, borderRadius: "50%", border: "1px solid rgba(255,255,255,.18)", background: "rgba(255,255,255,.06)", color: "rgba(255,255,255,.72)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", padding: 0 }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>
        </button>
        <div style={{ textAlign: "center", marginBottom: 26 }}>
          <img src="/goaa-logo.svg" alt="GOAA" width={48} height={48} style={{ display: "block", margin: "0 auto 16px", borderRadius: "50%", objectFit: "cover" }} />
          <h1 style={{ margin: 0, fontSize: 28, letterSpacing: "-.03em" }}>{mode === "register" ? "Create your GOAA account" : "Welcome to GOAA"}</h1>
          <p style={{ margin: "10px auto 0", color: "rgba(255,255,255,.62)", lineHeight: 1.6, fontSize: 14 }}>
            {mode === "register"
              ? "Register with your email — we\u0027ll send a one-time verification code."
              : hasPendingPurchase ? "Sign in before purchasing so we can save your pass and service progress." : hasSavedPrompt ? "Sign in to continue your new topic without losing current plans." : "Sign in to save your plans, conversations, and service progress."}
          </p>
        </div>

        {mode === "login" && (
          <>
            <div style={{ display: "grid", gap: 12 }}>
              {caps?.google && (
                <button type="button" style={buttonStyle} onClick={startGoogleSignIn}><span style={{ fontSize: 18, fontStyle: "italic", fontWeight: 700 }}>G</span>Continue with Google</button>
              )}
              {/* Apple / Phone: hidden (kept in DOM, not deleted) until wired */}
              <button type="button" style={{ ...buttonStyle, display: "none" }} onClick={() => socialUnavailable("Apple")}><span style={{ fontSize: 19 }}>Apple</span>Continue with Apple</button>
              <button type="button" style={{ ...buttonStyle, display: "none" }} onClick={() => socialUnavailable("phone")}><span style={{ fontSize: 18 }}>Phone</span>Continue with Phone</button>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 14, margin: "24px 0", color: "rgba(255,255,255,.46)", fontSize: 13 }}><span style={{ height: 1, flex: 1, background: "rgba(255,255,255,.14)" }} /><span>or</span><span style={{ height: 1, flex: 1, background: "rgba(255,255,255,.14)" }} /></div>

            <form onSubmit={handleLogin}>
              <input name="email" ref={emailRef} aria-label="Email" type="email" autoComplete="email" placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} style={inputStyle} />
              {showPassword && (
                <div style={{ position: "relative", marginTop: 12 }}>
                  <input
                    name="password"
                    ref={passwordRef}
                    aria-label="Password"
                    type={loginPwVisible ? "text" : "password"}
                    autoComplete="current-password"
                    placeholder="Password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    style={passwordInputStyle}
                  />
                  <PasswordRevealButton visible={loginPwVisible} onToggle={() => setLoginPwVisible((v) => !v)} />
                </div>
              )}
              <button type="submit" disabled={loading || !email.trim() || (showPassword && !password)} style={{ ...buttonStyle, marginTop: 12, border: 0, background: "#f4f4f5", color: "#111116", opacity: loading || !email.trim() || (showPassword && !password) ? .55 : 1 }}>{loading ? "Signing in..." : showPassword ? "Sign In" : "Continue"}</button>
            </form>

            {caps?.emailCode && (
              <p style={{ margin: "16px 0 0", textAlign: "center", fontSize: 14, color: "rgba(255,255,255,.62)" }}>
                New to GOAA?{" "}
                <button type="button" onClick={() => { setMode("register"); setRegStatus("") }} style={{ background: "transparent", border: 0, padding: 0, color: "#fff", fontSize: 14, textDecoration: "underline", textUnderlineOffset: 3, cursor: "pointer" }}>Create an account</button>
              </p>
            )}
          </>
        )}

        {mode === "register" && (
          regStep === "form" ? (
            <>
              <form onSubmit={handleSendCode}>
                <label style={labelStyle}>Email</label>
                <input aria-label="Registration email" type="email" autoComplete="email" placeholder="you@example.com" value={regEmail} onChange={(event) => setRegEmail(event.target.value)} style={inputStyle} />
                <button type="submit" disabled={regLoading || !regEmail.trim()} style={{ ...buttonStyle, marginTop: 16, border: 0, background: "#f4f4f5", color: "#111116", opacity: regLoading || !regEmail.trim() ? .55 : 1 }}>{regLoading ? "Sending…" : "Send verification code"}</button>
              </form>
              <p style={{ margin: "16px 0 0", textAlign: "center", fontSize: 13, color: "rgba(255,255,255,.5)", lineHeight: 1.6 }}>We\u0027ll email you a 6-digit code that expires in 10 minutes. No password is sent.</p>
              <p style={{ margin: "14px 0 0", textAlign: "center", fontSize: 14 }}>
                <button type="button" onClick={() => setMode("login")} style={{ background: "transparent", border: 0, padding: 0, color: "rgba(255,255,255,.62)", fontSize: 14, textDecoration: "underline", textUnderlineOffset: 3, cursor: "pointer" }}>Back to sign in</button>
              </p>
            </>
          ) : (
            <>
              <form onSubmit={handleRegister}>
                <label style={labelStyle}>Verification code <span style={{ color: "rgba(255,255,255,.4)", fontWeight: 400 }}>(sent to {regEmail.trim()})</span></label>
                <input aria-label="Verification code" inputMode="numeric" autoComplete="one-time-code" placeholder="6-digit code" value={regCode} onChange={(event) => setRegCode(event.target.value.replace(/\D/g, "").slice(0, 6))} style={inputStyle} />
                <label style={labelStyle}>Password</label>
                <div style={{ position: "relative" }}>
                  <input aria-label="Password" type={regPwVisible ? "text" : "password"} autoComplete="new-password" placeholder="At least 8 characters" value={regPassword} onChange={(event) => setRegPassword(event.target.value)} style={passwordInputStyle} />
                  <PasswordRevealButton visible={regPwVisible} onToggle={() => setRegPwVisible((v) => !v)} />
                </div>
                <label style={labelStyle}>Confirm password</label>
                <div style={{ position: "relative" }}>
                  <input aria-label="Confirm password" type={regPw2Visible ? "text" : "password"} autoComplete="new-password" placeholder="Re-enter your password" value={regPassword2} onChange={(event) => setRegPassword2(event.target.value)} style={passwordInputStyle} />
                  <PasswordRevealButton visible={regPw2Visible} onToggle={() => setRegPw2Visible((v) => !v)} />
                </div>
                <button type="submit" disabled={regLoading || regCode.length !== 6 || regPassword.length < 8 || regPassword !== regPassword2} style={{ ...buttonStyle, marginTop: 18, border: 0, background: "#f4f4f5", color: "#111116", opacity: regLoading || regCode.length !== 6 || regPassword.length < 8 || regPassword !== regPassword2 ? .55 : 1 }}>{regLoading ? "Creating account…" : "Create account"}</button>
              </form>
              <div style={{ margin: "16px 0 0", textAlign: "center" }}>
                {resendAfter > 0 ? (
                  <span style={{ color: "rgba(255,255,255,.45)", fontSize: 13 }}>Resend code in {resendAfter}s</span>
                ) : (
                  <button type="button" onClick={() => handleSendCode()} disabled={regLoading} style={{ background: "transparent", border: 0, padding: 0, color: "#fff", fontSize: 13, textDecoration: "underline", textUnderlineOffset: 3, cursor: "pointer", opacity: regLoading ? .55 : 1 }}>Resend code</button>
                )}
                <span style={{ color: "rgba(255,255,255,.3)", margin: "0 10px" }}>·</span>
                <button type="button" onClick={() => { setRegStep("form"); setRegStatus("") }} style={{ background: "transparent", border: 0, padding: 0, color: "rgba(255,255,255,.45)", fontSize: 13, textDecoration: "underline", textUnderlineOffset: 3, cursor: "pointer" }}>Change email</button>
              </div>
            </>
          )
        )}

        {(regStatus && mode === "register") && <div role="status" style={{ marginTop: 18, padding: "12px 14px", borderRadius: 12, background: "rgba(109,74,255,.10)", border: "1px solid rgba(109,74,255,.22)", color: "rgba(255,255,255,.78)", fontSize: 13, lineHeight: 1.5 }}>{regStatus}</div>}

        {mode === "login" && (
          <>
            <p style={{ margin: "18px 0 0", textAlign: "center", fontSize: 13, color: "rgba(255,255,255,.5)" }}>Not ready to sign in?</p>
            <div style={{ margin: "2px 0 0", textAlign: "center" }}>
              <button
                type="button"
                onClick={goAsGuest}
                style={{ background: "transparent", border: 0, padding: "4px 6px", color: "rgba(255,255,255,.5)", fontSize: 13, textDecoration: "underline", textUnderlineOffset: 3, cursor: "pointer" }}
              >Continue as guest</button>
            </div>
          </>
        )}

        {status && <div role="status" style={{ marginTop: 18, padding: "12px 14px", borderRadius: 12, background: justSignedInViaGoogle ? "rgba(52,199,123,.12)" : "rgba(109,74,255,.10)", border: `1px solid ${justSignedInViaGoogle ? "rgba(52,199,123,.3)" : "rgba(109,74,255,.22)"}`, color: "rgba(255,255,255,.78)", fontSize: 13, lineHeight: 1.5 }}>{status}</div>}

        <p style={{ margin: "22px 0 0", textAlign: "center", color: "rgba(255,255,255,.38)", fontSize: 11, lineHeight: 1.6 }}>
          By continuing you agree to GOAA&apos;s{" "}
          <a href="https://www.goaa.ai/terms" target="_blank" rel="noopener noreferrer" style={{ color: "rgba(255,255,255,.55)", textDecoration: "underline", textUnderlineOffset: 3 }}>Terms of Service</a>{" "}
          and{" "}
          <a href="https://www.goaa.ai/privacy" target="_blank" rel="noopener noreferrer" style={{ color: "rgba(255,255,255,.55)", textDecoration: "underline", textUnderlineOffset: 3 }}>Privacy Policy</a>.
        </p>
      </section>
    </main>
  )
}
