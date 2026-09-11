/**
 * server.ts — server-only helpers for the /agent-loop/* isolated front end.
 *
 * ISOLATION / HONESTY NOTES
 *   * This module runs on the C2 host only (Next.js server runtime).
 *   * The browser never receives the API session token: the BFF route stores
 *     it in an httpOnly cookie and re-attaches it as an explicit
 *     `Authorization: Bearer` header (the back end prefers Bearer over any
 *     ambient cookie).
 *   * When the Clerk entry is enabled, the token that travels upstream is the
 *     **Clerk session token** of the signed-in browser session. This module
 *     never asserts an identity of its own: the API verifies that token
 *     independently and derives the local user from `(issuer, subject)`.
 *   * The upstream base URL is read from the server-only environment variable
 *     GOAA_AGENT_LOOP_UPSTREAM and is resolved fail-closed: there is no
 *     default and no fallback, so a missing, malformed, non-loopback or
 *     non-allow-listed value disables proxying instead of quietly reaching
 *     some other environment.
 *   * No secret, password or token is hardcoded in this file. The Clerk
 *     **secret** key is never read to make a decision here: identity is
 *     verified downstream, by the API.
 */

import { cookies } from 'next/headers'
import { PUBLIC_PREFIX, UPSTREAM_PREFIX, toPublicUrl } from './shared'
import { clerkAuthState } from '../clerk-entry'

export { PUBLIC_PREFIX, UPSTREAM_PREFIX, toPublicUrl, clerkAuthState }

/** httpOnly cookie owned by the BFF; it holds the C2 API session token. */
export const SESSION_COOKIE = 'goaa_c2_ui_session'

/**
 * Ports the BFF is allowed to reach. The isolated test topology runs the
 * throwaway agent API on 127.0.0.1:3103 against the `goaa_c2test` database.
 * The long lived development API on 127.0.0.1:3101 (database `goaa_c2`) is
 * deliberately absent, so no environment value can point the browser at a
 * database this round must leave untouched.
 */
const ALLOWED_UPSTREAM_PORTS = new Set(['3103'])

const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '::1', '[::1]'])

/**
 * Resolve the upstream agent API base URL, or `null` when it is missing or
 * unsafe. Fail-closed by construction: anything that is not an explicit
 * http(s) loopback URL on an allow-listed port, with no path, query,
 * fragment or credentials, is rejected.
 */
export function upstreamBase(): string | null {
  const raw = process.env.GOAA_AGENT_LOOP_UPSTREAM
  if (!raw || !raw.trim()) return null
  let url: URL
  try {
    url = new URL(raw.trim())
  } catch {
    return null
  }
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return null
  if (url.username || url.password) return null
  if (url.search || url.hash) return null
  if (url.pathname !== '' && url.pathname !== '/') return null
  if (!LOOPBACK_HOSTS.has(url.hostname.toLowerCase())) return null
  const port = url.port || (url.protocol === 'https:' ? '443' : '80')
  if (!ALLOWED_UPSTREAM_PORTS.has(port)) return null
  return `${url.protocol}//${url.host}`
}

export type SessionUser = {
  id: string
  email: string
  full_name: string | null
  phone: string | null
  email_verified: boolean
  roles: string[]
  created_at: string
}

export type SessionInfo = {
  user: SessionUser
  application: { id: string; status: string } | null
}

export function sessionToken(): string | null {
  return cookies().get(SESSION_COOKIE)?.value || null
}

/**
 * The Clerk session token of the current request, or `null` when nobody is
 * signed in. The token is forwarded upstream verbatim; the API verifies it on
 * its own and never trusts a claim made by this tier.
 */
export async function clerkToken(): Promise<string | null> {
  const { auth } = await import('@clerk/nextjs/server')
  const { userId, getToken } = await auth()
  if (!userId) return null
  return (await getToken()) || null
}

/**
 * The token to forward upstream: the Clerk session token when Clerk is
 * switched on, otherwise the legacy BFF cookie session (Golden rollback path).
 *
 * A half configured deployment gets `null` — never the legacy session. Serving
 * a stale cookie session while the switch claims Clerk is on would be exactly
 * the kind of silent downgrade this candidate must not have.
 */
export async function requestToken(): Promise<string | null> {
  const state = clerkAuthState()
  if (state === 'enabled') return clerkToken()
  if (state === 'disabled') return sessionToken()
  return null
}

export async function upstreamFetch(
  path: string,
  token: string | null,
  init: RequestInit = {},
): Promise<Response> {
  const base = upstreamBase()
  if (!base) {
    throw new Error('GOAA_AGENT_LOOP_UPSTREAM is missing or is not an allowed loopback test endpoint')
  }
  const headers = new Headers(init.headers)
  headers.set('accept', 'application/json')
  if (token) headers.set('authorization', `Bearer ${token}`)
  return fetch(`${base}${UPSTREAM_PREFIX}${path}`, {
    ...init,
    headers,
    cache: 'no-store',
  })
}

export async function getSession(): Promise<SessionInfo | null> {
  const token = await requestToken()
  if (!token) return null
  try {
    const res = await upstreamFetch('/auth/me', token)
    if (!res.ok) return null
    const data = (await res.json()) as SessionInfo
    if (!data || !data.user) return null
    return data
  } catch {
    return null
  }
}

export function hasRole(user: SessionUser | null, role: string): boolean {
  return !!user && Array.isArray(user.roles) && user.roles.includes(role)
}
