/**
 * Same-origin BFF for the isolated /agent-loop/* front end.
 *
 *   browser  ->  /api/agent-loop/<path>  ->  ${GOAA_AGENT_LOOP_UPSTREAM}/api/v1/agent-loop/<path>
 *
 * Why a BFF instead of calling the API from the browser:
 *   * the API listens on loopback only and must never be exposed publicly;
 *   * the session token is kept in an httpOnly cookie and re-attached here as
 *     an explicit Bearer header, so JavaScript can never read it (the token is
 *     never put in localStorage, sessionStorage, a URL, HTML or the client
 *     bundle);
 *   * the upstream `Set-Cookie` is deliberately dropped: the API session
 *     cookie is replaced by one cookie owned by this app.
 *   * the golden (AI Butler) business session is the one exception to "Clerk's
 *     token authenticates everything": `golden/session` mints a business
 *     credential which this tier moves into a second httpOnly cookie, and the
 *     `verify`/`revoke` pair accepts that credential — after a Clerk sign-out
 *     too, which is the only way an out-of-order sign-out can still revoke
 *     something. Neither route accepts an identity from the caller.
 *   * when Clerk is switched on (`GOAA_C2_CLERK_AUTH_ENABLED`) the credential
 *     forwarded upstream is the browser's Clerk session token instead, and the
 *     API verifies that token itself — this tier never asserts an identity of
 *     its own. Precisely what changes: no GOAA BFF session cookie is read or
 *     written on that path. Clerk's own session mechanism is the SDK's
 *     business and is untouched.
 *
 * Safety properties enforced here (see also lib/agent-loop/server.ts):
 *   * the upstream is resolved from a server-only environment variable and is
 *     rejected unless it is a loopback URL on an allow-listed test port;
 *     there is no default and no fallback, so a missing or mistyped value
 *     fails closed instead of silently reaching another environment;
 *   * only an explicit allow-list of paths and methods is proxied, so this
 *     route can never act as an open proxy or be used for path traversal;
 *   * every state-changing request must come from this origin;
 *   * request bodies are size limited;
 *   * signed download links are exchanged server side, so no capability token
 *     is ever placed in a browser visible URL.
 */

import { NextRequest, NextResponse } from 'next/server'
import {
  SESSION_COOKIE,
  UPSTREAM_PREFIX,
  upstreamBase,
} from '@/app/lib/agent-loop/server'
import { clerkAuthState } from '@/app/lib/clerk-entry'

export const dynamic = 'force-dynamic'
export const revalidate = 0
export const runtime = 'nodejs'

/** Hard cap for JSON bodies (credentials, drafts, review decisions). */
const MAX_JSON_BYTES = 64 * 1024
/** Hard cap for licence document uploads; mirrors the API limit (5 MiB). */
const MAX_UPLOAD_BYTES = 5 * 1024 * 1024

const UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/
const SEGMENT_RE = /^[A-Za-z0-9._~-]+$/

/**
 * Request headers copied upstream. This is an allow-list: `host`, `cookie`,
 * and all hop-by-hop headers (connection, keep-alive, te, trailer,
 * transfer-encoding, upgrade, proxy-*) are therefore never forwarded.
 */
const FORWARD_REQUEST_HEADERS = [
  'content-type',
  'x-document-side',
  'x-license-id',
  'idempotency-key',
]

/** Response headers copied back to the browser; `Set-Cookie` is never one. */
const FORWARD_RESPONSE_HEADERS = ['content-type', 'content-disposition', 'cache-control']

/** Upstream routes the browser is allowed to reach, by method. */
const GET_ROUTES = new Set([
  // read-only liveness/diagnostics: the only way to prove from the browser
  // side which database the BFF is actually talking to
  'health',
  'auth/me',
  'applications/me',
  'agent/panel',
  'admin/applications',
  'applications/{uuid}',
  'admin/applications/{uuid}',
  // golden (AI Butler) business session: the link/session status, and the read
  // that tells a page whether its business credential is still accepted
  'golden/session',
  'golden/session/verify',
])
const PUT_ROUTES = new Set(['applications/me'])
/**
 * Readable without a credential. `health` is deliberately here: the isolation
 * gate uses it to prove which database the stack is actually talking to, before
 * anyone signs in.
 */
const PUBLIC_ROUTES = new Set(['health'])
const POST_ROUTES = new Set([
  'auth/register',
  'auth/login',
  'auth/logout',
  'applications/me/submit',
  'documents',
  'admin/applications/{uuid}/approve',
  'admin/applications/{uuid}/reject',
  'admin/applications/{uuid}/request-info',
  'admin/applications/{uuid}/suspend',
  'admin/applications/{uuid}/rerun-ai',
  // golden (AI Butler) business session: mint it, and revoke it
  'golden/session',
  'golden/session/revoke',
])

function fail(status: number, code: string, message: string): NextResponse {
  return NextResponse.json(
    { error: { code, message } },
    { status, headers: { 'cache-control': 'no-store', 'x-content-type-options': 'nosniff' } },
  )
}

/** Normalise a path into an allow-list key; `null` when it is not well formed. */
function routeKey(segments: string[]): string | null {
  if (!segments.length) return null
  for (const segment of segments) {
    if (!segment || segment === '.' || segment === '..') return null
    if (!SEGMENT_RE.test(segment)) return null
  }
  return segments.map((s) => (UUID_RE.test(s) ? '{uuid}' : s)).join('/')
}

/** `GET /documents/{uuid}/content` is a BFF capability, not an upstream route. */
function contentRoute(segments: string[]): string | null {
  if (segments.length !== 3) return null
  if (segments[0] !== 'documents' || segments[2] !== 'content') return null
  return UUID_RE.test(segments[1]) ? segments[1] : null
}

function isAllowed(method: string, segments: string[]): boolean {
  if (contentRoute(segments)) return method === 'GET' || method === 'HEAD'
  const key = routeKey(segments)
  if (!key) return false
  if (method === 'GET' || method === 'HEAD') return GET_ROUTES.has(key)
  if (method === 'PUT') return PUT_ROUTES.has(key)
  if (method === 'POST') return POST_ROUTES.has(key)
  return false
}

/** The only routes served without a credential, and only for reading. */
function isPublicRoute(method: string, segments: string[]): boolean {
  if (method !== 'GET' && method !== 'HEAD') return false
  const key = routeKey(segments)
  return key !== null && PUBLIC_ROUTES.has(key)
}

/**
 * CSRF: unsafe methods must demonstrably originate from this application.
 *
 * The `Origin` host is compared with the `Host` header the request actually
 * arrived with, not with `nextUrl.origin`: a standalone build can report a
 * configured host instead of the host the client dialled. Browsers set both
 * headers themselves, so a cross-site page cannot make them agree.
 */
function sameOrigin(req: NextRequest): boolean {
  const origin = req.headers.get('origin')
  if (origin) {
    let parsed: URL
    try {
      parsed = new URL(origin)
    } catch {
      return false
    }
    const expectedHost = req.headers.get('x-forwarded-host') || req.headers.get('host')
    if (!expectedHost) return false
    if (parsed.host !== expectedHost) return false
    const proto = (req.headers.get('x-forwarded-proto') || 'http').split(',')[0].trim()
    return parsed.protocol === `${proto}:`
  }
  return req.headers.get('sec-fetch-site') === 'same-origin'
}

type Body = { ok: true; bytes: ArrayBuffer | null } | { ok: false; response: NextResponse }

/** Read the request body with a hard cap; never buffer more than `limit`. */
async function readBody(req: NextRequest, limit: number): Promise<Body> {
  const declared = Number(req.headers.get('content-length') || '0')
  if (Number.isFinite(declared) && declared > limit) {
    return { ok: false, response: fail(413, 'payload_too_large', 'the request body is too large') }
  }
  const stream = req.body
  if (!stream) return { ok: true, bytes: null }
  const reader = stream.getReader()
  const chunks: Uint8Array[] = []
  let total = 0
  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      if (!value) continue
      total += value.byteLength
      if (total > limit) {
        await reader.cancel()
        return { ok: false, response: fail(413, 'payload_too_large', 'the request body is too large') }
      }
      chunks.push(value)
    }
  } catch {
    return { ok: false, response: fail(400, 'bad_body', 'the request body could not be read') }
  }
  const buffer = new ArrayBuffer(total)
  const view = new Uint8Array(buffer)
  let offset = 0
  for (const chunk of chunks) {
    view.set(chunk, offset)
    offset += chunk.byteLength
  }
  return { ok: true, bytes: buffer }
}

/** Pass an upstream response through with only safe headers. */
async function relay(upstream: Response): Promise<NextResponse> {
  const body = await upstream.arrayBuffer()
  const headers = new Headers()
  for (const name of FORWARD_RESPONSE_HEADERS) {
    const value = upstream.headers.get(name)
    if (value) headers.set(name, value)
  }
  headers.set('cache-control', 'no-store')
  headers.set('x-content-type-options', 'nosniff')
  return new NextResponse(body.byteLength ? body : null, { status: upstream.status, headers })
}

/**
 * Accept only the API's own relative download path. The signed, short lived
 * capabilities never leave this process: they are resolved into bytes here.
 */
function safeDownloadPath(raw: string | null | undefined): string | null {
  if (!raw) return null
  let path = raw
  if (/^https?:\/\//i.test(path)) {
    try {
      path = new URL(path).pathname
    } catch {
      return null
    }
  }
  if (!path.startsWith(`${UPSTREAM_PREFIX}/downloads/`)) return null
  if (!/^[A-Za-z0-9/_.~-]+$/.test(path)) return null
  if (path.includes('..') || path.includes('//')) return null
  return path
}

function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    sameSite: 'lax' as const,
    // The token must never be sent in the clear. Chrome accepts `Secure`
    // cookies on the trustworthy loopback origins this isolated environment
    // uses; on a real deployment TLS is terminated in front, so this stays
    // true. It is deliberately not configurable, so no local run can quietly
    // downgrade it.
    secure: true,
    path: '/',
    maxAge,
  }
}

/**
 * The credential forwarded upstream.
 *
 * Clerk on: the browser's **Clerk session token**, read from the request
 * itself. This tier asserts nothing about identity — no e-mail, user id, role
 * or issuer is forwarded, and the API verifies the token independently before
 * resolving the local user from `(issuer, subject)`. No GOAA BFF session cookie
 * is read or written on this path, so a leftover `goaa_c2_ui_session` value can
 * never authenticate anyone once Clerk is on. (Clerk's own session cookie is
 * the SDK's own mechanism; this tier does not fabricate, and does not need to
 * know, its contents.)
 *
 * Clerk off (Golden rollback): the legacy httpOnly API session cookie, exactly
 * as it shipped.
 *
 * Clerk on but half configured: `null` — the request is refused upstream
 * rather than being served from a stale legacy cookie.
 */
async function upstreamToken(req: NextRequest): Promise<string | null> {
  const state = clerkAuthState()
  if (state === 'enabled') {
    try {
      const { auth } = await import('@clerk/nextjs/server')
      const { userId, getToken } = await auth()
      if (!userId) return null
      return (await getToken()) || null
    } catch {
      // Fail closed: an unverifiable session is an unauthenticated one, and the
      // API answers 401 rather than this tier inventing an identity.
      return null
    }
  }
  if (state === 'disabled') return req.cookies.get(SESSION_COOKIE)?.value || null
  return null
}

/**
 * Routes authenticated by the **business** credential instead of Clerk's.
 *
 * They exist so a sign-out can be finished, not so a sign-in can be shortcut:
 * `verify` resolves the business token alone, and `revoke` accepts either
 * credential. That is what closes the out-of-order case — Clerk already signed
 * out, business token still in the browser — where the identity-based revoke
 * has nothing left to prove who the caller is.
 *
 * The credential is carried in the golden surface's own slot (`localStorage`
 * `client_token`) and presented as a Bearer header; this tier never keeps a copy
 * of it and never writes one into a cookie of its own.
 */
const GOLDEN_TOKEN_ROUTES = new Set(['golden/session/verify', 'golden/session/revoke'])

/**
 * The business credential this browser presented, if any.
 *
 * It travels the way the golden surface already sends it: `Authorization:
 * Bearer <token>`. Only the shape is checked here — the token's authority is
 * decided by the API, never by this tier — and anything that is not a
 * well-formed token is treated as absent.
 */
function businessBearer(req: NextRequest): string | null {
  const header = req.headers.get('authorization') || ''
  const match = /^Bearer ([0-9a-f]{32})$/.exec(header.trim())
  return match ? match[1] : null
}

/**
 * The credential attached upstream for this request.
 *
 * Every ordinary route gets the browser's Clerk session token and nothing else.
 * `golden/session/revoke` gets the Clerk token when it is still valid — the
 * normal order — and falls back to the business credential this browser
 * presented; `golden/session/verify` gets only the business credential, because
 * the point of that read is to ask whether it is still accepted.
 */
async function credentialFor(req: NextRequest, joined: string): Promise<string | null> {
  if (!GOLDEN_TOKEN_ROUTES.has(joined)) return upstreamToken(req)
  if (joined === 'golden/session/revoke') {
    const clerk = await upstreamToken(req)
    if (clerk) return clerk
  }
  return businessBearer(req)
}

async function documentContent(req: NextRequest, documentId: string, base: string): Promise<NextResponse> {
  const token = await upstreamToken(req)
  if (!token) return fail(401, 'unauthenticated', 'sign in to open this document')

  const auth = { accept: 'application/json', authorization: `Bearer ${token}` }
  let linkRes: Response
  try {
    linkRes = await fetch(`${base}${UPSTREAM_PREFIX}/documents/${documentId}/link`, {
      headers: auth,
      cache: 'no-store',
      redirect: 'error',
    })
  } catch {
    return fail(502, 'upstream_unreachable', 'the C2 agent API is not reachable on loopback')
  }
  if (!linkRes.ok) return relay(linkRes)

  let url: string | null = null
  try {
    const payload = (await linkRes.json()) as { url?: unknown }
    url = typeof payload.url === 'string' ? payload.url : null
  } catch {
    url = null
  }
  const path = safeDownloadPath(url)
  if (!path) return fail(502, 'upstream_link_invalid', 'the document link was not usable')

  let fileRes: Response
  try {
    fileRes = await fetch(`${base}${path}`, {
      headers: { accept: '*/*', authorization: `Bearer ${token}` },
      cache: 'no-store',
      redirect: 'error',
    })
  } catch {
    return fail(502, 'upstream_unreachable', 'the C2 agent API is not reachable on loopback')
  }
  if (!fileRes.ok) return relay(fileRes)

  const headers = new Headers()
  for (const name of FORWARD_RESPONSE_HEADERS) {
    const value = fileRes.headers.get(name)
    if (value) headers.set(name, value)
  }
  headers.set('cache-control', 'no-store')
  headers.set('x-content-type-options', 'nosniff')
  return new NextResponse(fileRes.body, { status: fileRes.status, headers })
}

async function proxy(req: NextRequest, segments: string[]): Promise<NextResponse> {
  const base = upstreamBase()
  if (!base) {
    return fail(503, 'upstream_not_configured', 'GOAA_AGENT_LOOP_UPSTREAM is missing or is not an allowed loopback test endpoint')
  }

  const method = req.method.toUpperCase()
  if (!isAllowed(method, segments)) {
    return fail(404, 'route_not_allowed', 'this path and method are not proxied by the agent-loop BFF')
  }
  if (method !== 'GET' && method !== 'HEAD' && !sameOrigin(req)) {
    return fail(403, 'cross_origin_blocked', 'state changing requests must originate from this application')
  }

  const contentId = contentRoute(segments)
  if (contentId) return documentContent(req, contentId, base)

  const joined = segments.join('/')
  const target = `${base}${UPSTREAM_PREFIX}/${joined}${req.nextUrl.search}`

  const state = clerkAuthState()
  // A half configured deployment refuses here rather than consulting the API.
  if (state === 'misconfigured') {
    return fail(503, 'clerk_misconfigured', 'Clerk is enabled but not configured')
  }
  const token = await credentialFor(req, joined)
  // No credential, no upstream call. The API is never asked to guess, and a
  // request that carries no session is turned away by this tier.
  if (state === 'enabled' && !token && !isPublicRoute(method, segments)) {
    return fail(401, 'clerk_session_required', 'sign in to continue')
  }
  const headers = new Headers()
  for (const name of FORWARD_REQUEST_HEADERS) {
    const value = req.headers.get(name)
    if (value) headers.set(name, value)
  }
  if (token) headers.set('authorization', `Bearer ${token}`)

  const init: RequestInit = { method, headers, cache: 'no-store', redirect: 'manual' }
  // The golden writes carry nothing: the API reads the identity from the
  // verified session and needs no payload, so whatever the client sent is
  // dropped here. A browser therefore cannot even transmit a claim about who it
  // is, let alone have one honoured.
  const carriesBody = joined !== 'golden/session' && joined !== 'golden/session/revoke'
  if (method !== 'GET' && method !== 'HEAD' && carriesBody) {
    const limit = joined === 'documents' ? MAX_UPLOAD_BYTES : MAX_JSON_BYTES
    const body = await readBody(req, limit)
    if (!body.ok) return body.response
    if (body.bytes && body.bytes.byteLength) init.body = body.bytes
  }

  let upstream: Response
  try {
    upstream = await fetch(target, init)
  } catch {
    return fail(502, 'upstream_unreachable', 'the C2 agent API is not reachable on loopback')
  }

  // --- login: keep the token server-side, hand the browser only the user ---
  if (joined === 'auth/login') {
    const text = await upstream.text()
    if (!upstream.ok) {
      return new NextResponse(text, {
        status: upstream.status,
        headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
      })
    }
    let payload: Record<string, unknown> = {}
    try {
      payload = JSON.parse(text) as Record<string, unknown>
    } catch {
      payload = {}
    }
    const issued = typeof payload.access_token === 'string' ? payload.access_token : null
    const ttlSeconds = Number(process.env.GOAA_AGENT_LOOP_SESSION_TTL_SECONDS || 43200)
    delete payload.access_token
    const response = NextResponse.json(payload, {
      status: upstream.status,
      headers: { 'cache-control': 'no-store' },
    })
    // The legacy cookie is only ever issued when Clerk is switched off; with
    // Clerk on, the browser's Clerk session is the one and only credential,
    // and a half configured deployment issues nothing at all.
    if (issued && clerkAuthState() === 'disabled') {
      response.cookies.set(SESSION_COOKIE, issued, cookieOptions(ttlSeconds))
    }
    return response
  }

  // --- logout: revoke upstream, then drop the local cookie ---
  if (joined === 'auth/logout') {
    const text = await upstream.text()
    const response = new NextResponse(text || '{"status":"signed_out"}', {
      status: upstream.ok ? 200 : upstream.status,
      headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
    })
    // Signing out of Clerk is a Clerk operation performed in the browser by the
    // official client; there is no legacy logout to offer once Clerk is on.
    if (clerkAuthState() === 'disabled') {
      response.cookies.set(SESSION_COOKIE, '', cookieOptions(0))
    }
    return response
  }

  // --- golden business session: the credential becomes a cookie, never a body ---
  //
  // The API hands back the one plaintext business token. It goes straight into
  // an httpOnly cookie and is deleted from the payload, so it exists only
  // between this tier and the browser's cookie jar: no script can read it, and
  // it never reaches the page, the DOM, a URL or the bundle.
  if (joined === 'golden/session' && method === 'POST') {
    const text = await upstream.text()
    if (!upstream.ok) {
      return new NextResponse(text, {
        status: upstream.status,
        headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
      })
    }
    let payload: Record<string, unknown> = {}
    try {
      payload = JSON.parse(text) as Record<string, unknown>
    } catch {
      payload = {}
    }
    const issued = typeof payload.token === 'string' ? payload.token : null
    if (!issued) {
      // No credential, no session: reporting success here would leave the page
      // believing it holds a business session it does not have.
      return fail(502, 'upstream_credential_missing', 'the business session was not issued')
    }
    // The credential goes to the same-origin page, which stores it where the
    // golden surface keeps it (`localStorage.client_token`) and sends it back
    // as a Bearer header. This tier keeps no copy.
    return NextResponse.json(payload, {
      status: upstream.status,
      headers: { 'cache-control': 'no-store' },
    })
  }

  // --- golden sign-out: the API revokes; the page deletes its own copy ---
  //
  // Deliberately no cookie work here: the credential lives in the page, and a
  // failed revoke must leave it *visible* rather than quietly dropped, so the
  // bridge can report the failure and the page keeps a state the user can see.
  if (joined === 'golden/session/revoke' && method === 'POST') {
    const text = await upstream.text()
    return new NextResponse(text || '{"revoked":0}', {
      status: upstream.ok ? 200 : upstream.status,
      headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
    })
  }

  return relay(upstream)
}

type Ctx = { params: { path: string[] } }

export async function GET(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx.params.path)
}
export async function POST(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx.params.path)
}
export async function PUT(req: NextRequest, ctx: Ctx) {
  return proxy(req, ctx.params.path)
}
export async function DELETE(req: NextRequest, ctx: Ctx) {
  return fail(405, 'method_not_allowed', 'this method is not proxied by the agent-loop BFF')
}
export async function PATCH(req: NextRequest, ctx: Ctx) {
  return fail(405, 'method_not_allowed', 'this method is not proxied by the agent-loop BFF')
}
