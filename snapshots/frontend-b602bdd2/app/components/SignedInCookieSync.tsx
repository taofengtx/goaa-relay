"use client"

// Cross-origin signed-in flag hygiene (2026-09-04).
//
// On every page load this component removes the goaa_signed_in flag cookie
// when the planning origin has no client_token in localStorage. This prevents
// a stale homepage "signed-in" state from lingering after the localStorage
// session is gone (e.g. storage cleared in another flow, cookie left behind
// by an interrupted logout). Removal is a guarded no-op outside goaa.ai hosts
// and touches ONLY the flag cookie — never tokens or other cookies.
import { useEffect } from "react"
import { clearSignedInCookieFromDocument, hasSignedInCookie } from "../lib/goaa-cookie"

export default function SignedInCookieSync() {
  useEffect(() => {
    try {
      if (typeof window === "undefined" || typeof document === "undefined") return
      const hasToken = Boolean(window.localStorage.getItem("client_token"))
      if (!hasToken && hasSignedInCookie(window.document.cookie)) {
        clearSignedInCookieFromDocument()
      }
    } catch {
      // hygiene only; never break the page on storage exceptions
    }
  }, [])
  return null
}
