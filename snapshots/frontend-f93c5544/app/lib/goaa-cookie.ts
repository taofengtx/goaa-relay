// GOAA signed-in flag cookie mirror (2026-09-04).
//
// Purpose: expose a lightweight, cross-origin "is a customer signed in?"
// signal from the planning app (planning.goaa.ai) to the marketing homepage
// served by Framer (www.goaa.ai). Same-registrable-domain cookies set from a
// subdomain with Domain=.goaa.ai are readable on the whole .goaa.ai space.
//
// SECURITY: this cookie contains ONLY a boolean flag (value "1"). It NEVER
// carries the client token, username, email, order id, or any other
// identifying content. The real session still lives in localStorage on the
// planning origin; the cookie is only a presence mirror and is cleared
// together with the customer session.
//
// Non-goaa.ai hosts (localhost, IP previews, other preview hosts) skip the
// cookie entirely so dev/preview never trips on a Domain attribute mismatch.
// The write/clear builders and host rule are pure so they are unit-testable
// without a DOM.

export const GOAA_SIGNED_IN_COOKIE = 'goaa_signed_in'

// Login does not return an expiry; the planning client token is issued with a
// 30-day validity, so the mirror cookie uses the same 30-day max age.
export const GOAA_SIGNED_IN_MAX_AGE_SECONDS = 2592000
export const GOAA_COOKIE_DOMAIN = '.goaa.ai'

export function cookieDomainForHost(hostname: string | null | undefined): string | null {
  const host = (hostname || '').trim().toLowerCase()
  if (host === 'goaa.ai' || host.endsWith('.goaa.ai')) return GOAA_COOKIE_DOMAIN
  return null
}

export function buildSignedInSetCookie(
  domain: string | null,
  maxAgeSeconds: number = GOAA_SIGNED_IN_MAX_AGE_SECONDS,
): string {
  const parts = [`${GOAA_SIGNED_IN_COOKIE}=1`, 'Path=/']
  if (domain) parts.push(`Domain=${domain}`)
  parts.push(`Max-Age=${maxAgeSeconds}`, 'Secure', 'SameSite=Lax')
  return parts.join('; ')
}

export function buildSignedInClearCookie(domain: string | null): string {
  const parts = [`${GOAA_SIGNED_IN_COOKIE}=`, 'Path=/']
  if (domain) parts.push(`Domain=${domain}`)
  parts.push('Max-Age=0')
  return parts.join('; ')
}

export function parseCookieHeader(cookieHeader: string | null | undefined): Record<string, string> {
  const out: Record<string, string> = {}
  if (!cookieHeader) return out
  for (const part of cookieHeader.split(';')) {
    const eq = part.indexOf('=')
    if (eq < 0) continue
    const key = part.slice(0, eq).trim()
    const value = part.slice(eq + 1).trim()
    if (key) out[key] = value
  }
  return out
}

export function hasSignedInCookie(cookieHeader: string | null | undefined): boolean {
  if (!cookieHeader) return false
  const value = parseCookieHeader(cookieHeader)[GOAA_SIGNED_IN_COOKIE]
  return typeof value === 'string' && value !== ''
}

function currentCookieDomain(): string | null {
  if (typeof window === 'undefined' || typeof window.location === 'undefined') return null
  return cookieDomainForHost(window.location.hostname)
}

// Write the mirror flag cookie. No-op on non-goaa.ai hosts (dev/preview) and
// when no DOM exists (SSR/tests).
export function writeSignedInCookieToDocument(): void {
  const domain = currentCookieDomain()
  if (!domain) return
  try {
    window.document.cookie = buildSignedInSetCookie(domain)
  } catch {
    // ignore storage exceptions on unusual hosts
  }
}

// Clear the mirror flag cookie (same name/Domain/Path, Max-Age=0). No-op on
// non-goaa.ai hosts and when no DOM exists.
export function clearSignedInCookieFromDocument(): void {
  const domain = currentCookieDomain()
  if (!domain) return
  try {
    window.document.cookie = buildSignedInClearCookie(domain)
  } catch {
    // ignore storage exceptions on unusual hosts
  }
}
