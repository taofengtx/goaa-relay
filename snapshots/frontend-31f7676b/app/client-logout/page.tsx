'use client'

// Secure client sign-out landing (2026-09-04).
//
// Fixed URL: https://planning.goaa.ai/client-logout
// - Runs ONLY on planning.goaa.ai origin, reusing app/lib/customer-signout.ts
//   (clearCustomerSession) — the exact same whitelist + butler nickname
//   migration used by the in-app account menu. No second logout logic exists.
// - Clears customer identity / current order / tied temp state; PRESERVES
//   goaa_planning_workspace_v1, butler nicknames (migrated to guest), demo and
//   unrelated site preferences. Never clears whole storage (no clear-all API).
// - No order / match / checkout / payment / account-delete API calls.
// - Returns to the FIXED address https://goaa.ai/?logged_out=1 only.
//   The ONLY accepted query value is return=home (fixed enum); any other value
//   is ignored. No arbitrary/external return URLs => no open redirect.
// - Visitors who arrive signed-out still run the (idempotent) whitelist
//   cleanup and are safely returned home without errors or business requests.
import { useEffect, useRef } from 'react'
import { clearCustomerSession } from '../lib/customer-signout'

const HOME_AFTER_LOGOUT = 'https://goaa.ai/?logged_out=1'
const ALLOWED_RETURN_VALUES: readonly string[] = ['home']

export default function ClientLogoutPage() {
  const ranRef = useRef(false)

  useEffect(() => {
    if (ranRef.current || typeof window === 'undefined') return
    ranRef.current = true

    // Parse & validate. Only return=home is accepted; anything else is
    // ignored. The value is NEVER used to build the destination URL.
    const params = new URLSearchParams(window.location.search)
    const requested = params.get('return')
    if (requested !== null && !ALLOWED_RETURN_VALUES.includes(requested)) {
      // invalid enum: ignore silently, still perform the standard cleanup and
      // go to the fixed home destination (do not pass params through).
      params.delete('return')
    }

    // Same whitelisted cleanup the account menu uses (idempotent).
    clearCustomerSession(window.localStorage, window.sessionStorage)

    // Brief visible status with accessible announcement, then fixed redirect.
    const t = window.setTimeout(() => {
      window.location.assign(HOME_AFTER_LOGOUT)
    }, 600)
    return () => window.clearTimeout(t)
  }, [])

  return (
    <main className="goaa-logout-page" aria-live="polite">
      <p role="status">正在安全退出……</p>
      <p className="goaa-logout-sub">即将返回 GOAA.ai 首页</p>
    </main>
  )
}
