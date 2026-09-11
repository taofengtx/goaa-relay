"use client"

import { useEffect, useState } from "react"
import { usePathname } from "next/navigation"

const AUTH_RETURN_KEY = "goaa_auth_return_v1"
// Canonical purchase journey: authentication → formal order → Order Engine
// checkout → Stripe → webhook → connectPaid → matching → customer workspace.
const CONNECT_PASS_TARGET = "/connect-pass?source=planning"
// P4.4B: ChatComponent dispatches this event while a consultation is active;
// the top bar hides so it never dominates/overlaps the consultation flow.
const CONSULTATION_EVENT = "goaa:consultation-active"

function hasClientSession() {
  return typeof window !== "undefined" && Boolean(window.localStorage.getItem("client_token"))
}

export default function ProfessionalConnectBar() {
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)
  const [consultationActive, setConsultationActive] = useState(false)

  // Subtle optional navigation entry on the entry/dashboard pages; hidden
  // while the user is actively inside the consultation flow.
  const visible = (pathname === "/" || pathname === "/client-dashboard") && !consultationActive

  useEffect(() => {
    setMounted(true)
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<{ active: boolean }>).detail
      setConsultationActive(Boolean(detail?.active))
    }
    window.addEventListener(CONSULTATION_EVENT, handler)
    return () => window.removeEventListener(CONSULTATION_EVENT, handler)
  }, [])

  if (!visible) return null

  function handleConnect() {
    if (!mounted) return
    if (!hasClientSession()) {
      // Formal Customer Auth return flow: after sign-in, continue the canonical journey.
      window.localStorage.setItem(AUTH_RETURN_KEY, CONNECT_PASS_TARGET)
      window.location.assign("/client-login?resume=1&reason=purchase")
      return
    }
    window.location.assign(CONNECT_PASS_TARGET)
  }

  return (
    <>
      <div className="goaa-professional-connect goaa-paid-open-only" role="region" aria-label="Connect with a Professional">
        <div className="goaa-professional-connect-copy">
          <strong>Need a professional to handle this directly?</strong>
          <span>One-time connection fee · 30-day access · No automatic renewal</span>
        </div>
        <button type="button" className="goaa-professional-connect-cta" onClick={handleConnect}>
          Connect Now · $39.90
        </button>
      </div>
    </>
  )
}
