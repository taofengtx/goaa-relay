import { NextResponse, type NextFetchEvent, type NextRequest } from "next/server"
import { clerkMiddleware } from "@clerk/nextjs/server"

import {
  CLERK_ENTRY_MARKER,
  CLERK_ENTRY_MARKER_VALUE,
  CLERK_ENTRY_PATH,
  RETIRED_LOGIN_PATHS,
  clerkAuthState,
  clerkMisconfiguredDetail,
  isUnifiedLoginPath,
  retiredEntryRedirect,
  trimTrailingSlash,
  unifiedEntryNext,
} from "./app/lib/clerk-entry"

/**
 * P4.3B — Production-only internal/test route exposure guard.
 *
 * This middleware is an environment + route exposure guard. It never reads
 * customer/agent/admin localStorage tokens and never makes auth decisions.
 * Existing page guards and the Order Engine backend require_auth/role checks
 * remain authoritative.
 *
 * Internal/test/demo routes are blocked (404) in production and allowed in
 * Vercel Preview and local development so Tao can keep verifying flows.
 *
 * CLERK ENTRY TRANSITION (C2 test only, off unless the switch says otherwise)
 *   `GOAA_C2_CLERK_AUTH_ENABLED` is the single switch, shared with the backend:
 *     * off (or absent)  -> the legacy path runs untouched;
 *     * on + configured  -> the official `clerkMiddleware()` wraps the
 *       transition so that `auth()`/`getToken()` work downstream, the
 *       *test-only* `/agent-loop/login` alias answers with a server-side
 *       redirect to the one public entry point, and every `/client-login`
 *       visit is internally rewritten to the Clerk sign-in route — its source
 *       file stays byte-identical. A valid `next` is kept; a missing or
 *       rejected one lands on `/planning` (Round C1.7: the legacy
 *       email+password form is retired while Clerk is in charge).
 *     * on + incomplete  -> refuse. A half configured deployment must not
 *       quietly serve the legacy flow, and we must not swallow the error.
 *
 * GOLDEN ROUTES ARE NOT TOUCHED. `/agent-login` is the golden build's own
 * sign-in page, not a retired alias: it is served exactly as before under both
 * switch states, and every landing this file computes is either under
 * `/agent-loop` or exactly `/planning` — never a golden dashboard.
 *
 * The transition itself decides nothing about identity: it only routes, and an
 * invalid `next` is replaced by a fixed default, never repaired.
 */

const INTERNAL_PREFIX_ROUTES = [
  "/order-live",
  "/full-flow-live",
  "/order-demo",
  "/full-flow-demo",
  "/agent-order-demo",
  "/admin-dashboard",
  "/agent-skill-engine",
] as const

// Exact-only on purpose: /customer-order must never match the formal product
// route /customer-order-live.
const INTERNAL_EXACT_ROUTES = [
  "/customer-order",
  "/agent-dashboard/service-orders",
  "/agent-dashboard/order-workspace",
  "/agent-dashboard/ai-lab",
] as const

/** Surfaces that only exist because Clerk is the identity provider. */
const CLERK_DEPENDENT_PREFIXES = ["/agent-loop", "/api/agent-loop"] as const

function matchesPrefix(pathname: string, route: string): boolean {
  return pathname === route || pathname === `${route}/` || pathname.startsWith(`${route}/`)
}

function isInternalRoute(pathname: string): boolean {
  for (const route of INTERNAL_EXACT_ROUTES) {
    if (pathname === route || pathname === `${route}/`) return true
  }
  for (const route of INTERNAL_PREFIX_ROUTES) {
    if (matchesPrefix(pathname, route)) return true
  }
  return false
}

/**
 * Fail-safe environment gate.
 *
 *  - VERCEL_ENV === "preview" | "development"  -> allow (preview verification)
 *  - VERCEL_ENV === "production"               -> block
 *  - VERCEL_ENV missing (self-host / unknown / local):
 *      allow only when NODE_ENV is not "production" (plain `next dev`),
 *      otherwise block. A production-optimized build with a missing optional
 *      env var must fail safe toward blocking, never exposing internal
 *      routes. Note we do NOT rely on NODE_ENV alone, because Vercel Preview
 *      builds also run with NODE_ENV=production.
 */
function internalRoutesAllowed(): boolean {
  const env = process.env.VERCEL_ENV
  if (env === "preview" || env === "development") return true
  if (env === "production") return false
  return process.env.NODE_ENV !== "production"
}

function exposureGuard(request: NextRequest): NextResponse | null {
  if (isInternalRoute(request.nextUrl.pathname) && !internalRoutesAllowed()) {
    return new NextResponse("Not Found", { status: 404 })
  }
  return null
}

/**
 * The request headers the downstream page is allowed to see.
 *
 * The marker is always rebuilt from scratch, so a client copy never survives.
 */
function forwardHeaders(request: NextRequest, marker?: string): Headers {
  const headers = new Headers()
  request.headers.forEach((value, key) => {
    if (key.toLowerCase() !== CLERK_ENTRY_MARKER) headers.set(key, value)
  })
  if (marker) headers.set(CLERK_ENTRY_MARKER, marker)
  return headers
}

/**
 * Hand the chosen headers downstream.
 *
 * The override list is written out explicitly rather than left to be inferred:
 * a decorator downstream (Clerk's own `clerkMiddleware`) re-seeds the
 * downstream headers from the *original* request whenever that list is missing,
 * which would pass a forged marker straight through to the page. (A request
 * with no headers other than the marker has nothing left to list; the Next
 * server always supplies at least `host`.)
 */
function withForwardedHeaders(response: NextResponse, headers: Headers): NextResponse {
  const keys = [...headers.keys()]
  response.headers.set("x-middleware-override-headers", keys.join(","))
  for (const [key, value] of headers) response.headers.set(`x-middleware-request-${key}`, value)
  return response
}

/** The loopback spellings a client may use to reach this test service. */
const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"])

/**
 * The origin this service is configured to run on — server configuration only.
 *
 * Next decides whether a middleware rewrite is internal by comparing it with
 * the origin it builds for itself in `resolve-routes.js`:
 *
 *   initUrl = `${protocol}://${formatHostname(opts.hostname || "localhost")}:${opts.port}${req.url}`
 *
 * where `opts.hostname`/`opts.port` are this service's own `HOSTNAME` and
 * `PORT` (the standalone server passes exactly those to `startServer`). The
 * same service reached under another loopback spelling — `127.0.0.1` instead
 * of `localhost`, or through a forwarder's port — then produces a rewrite
 * whose origin differs from `initUrl`, so Next classifies it as external and
 * proxies it back to the server it is already talking to: observed on the 3102
 * test service as `Failed to proxy http://localhost:3102/...` / socket hang
 * up / HTTP 500.
 *
 * The value below is therefore configuration and nothing else. No request
 * header takes part in it: a client supplied `Host`, `X-Forwarded-Host`,
 * `X-Forwarded-Proto` or `Forwarded` header must never be able to move a
 * rewrite to another origin. The `HOSTNAME || "localhost"` fallback only
 * mirrors Next's own fallback, so both sides compute the same string. Without
 * a usable `PORT` or `HOSTNAME` there is no origin to unify to and callers
 * leave the response alone.
 */
function selfOrigin(): string | null {
  const port = (process.env.PORT || "").trim()
  if (!/^[0-9]{1,5}$/.test(port)) return null
  const configured = (process.env.HOSTNAME || "localhost").trim().toLowerCase()
  const hostname = configured.replace(/^\[|\]$/g, "")
  if (!hostname || !/^[a-z0-9.:-]+$/.test(hostname)) return null
  const host = hostname.includes(":") ? `[${hostname}]` : hostname
  return `http://${host}:${port}`
}

/**
 * Next's middleware sandbox requires an absolute rewrite URL: before the
 * response leaves the sandbox its adapter parses the header with
 * `new NextURL(value)`, and a path-only value throws `ERR_INVALID_URL`
 * (observed on the 3102 test service). Rewrites therefore stay absolute.
 *
 * Only this service's own loopback rewrite has its host spelling replaced, and
 * only when the target already names this service exactly: loopback host, this
 * service's scheme (`http` — 3102 speaks HTTP with no TLS terminator in front
 * of it) and this service's configured port. A rewrite to another port (e.g.
 * a different local service), to a non-loopback host, an `https` or relative
 * or unparsable value, or a service without a usable `PORT`/`HOSTNAME`, is
 * returned exactly as it arrived.
 *
 * Path, query and every other header are untouched: Clerk's decorated request
 * headers, the entry marker, and a redirect's `Location` all survive.
 */
function unifyLoopbackRewriteOrigin<T extends Response>(response: T): T {
  const raw = response.headers.get("x-middleware-rewrite")
  if (!raw) return response
  let target: URL
  try {
    target = new URL(raw)
  } catch {
    return response // not an absolute URL: nothing to unify
  }
  const bare = (hostname: string) => hostname.replace(/^\[|\]$/g, "")
  if (!LOOPBACK_HOSTS.has(bare(target.hostname))) return response
  const origin = selfOrigin()
  if (!origin) return response
  let self: URL
  try {
    self = new URL(origin)
  } catch {
    return response // unusable configured origin: leave the rewrite alone
  }
  if (target.protocol !== self.protocol) return response
  if (target.port !== self.port) return response
  const unified = `${origin}${target.pathname}${target.search}`
  if (unified !== raw) response.headers.set("x-middleware-rewrite", unified)
  return response
}

/** True when serving this path the legacy way would be serving stale auth. */
function isClerkDependent(request: NextRequest): boolean {
  const { pathname } = request.nextUrl
  if (pathname === CLERK_ENTRY_PATH) return true
  if ((RETIRED_LOGIN_PATHS as readonly string[]).includes(trimTrailingSlash(pathname))) return true
  // Every /client-login visit is the Clerk card now; a half configured
  // deployment must refuse it rather than show the retired form.
  if (isUnifiedLoginPath(pathname)) return true
  return CLERK_DEPENDENT_PREFIXES.some((prefix) => matchesPrefix(pathname, prefix))
}

function misconfigured(request: NextRequest): NextResponse {
  if (!isClerkDependent(request)) return NextResponse.next()
  // Variable NAMES only — never a value, a length or a fragment.
  const missing = clerkMisconfiguredDetail().join(", ")
  return new NextResponse(`Clerk is enabled but not configured: ${missing}\n`, {
    status: 503,
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" },
  })
}

/**
 * Routing only. Runs inside the official middleware, so it applies after Clerk
 * has decorated the request, and its response is decorated in turn.
 */
function entryTransition(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl

  const retired = retiredEntryRedirect(pathname)
  if (retired) return NextResponse.redirect(new URL(retired, request.url))

  if (isUnifiedLoginPath(pathname)) {
    // Round C1.7: the public entry always opens the Clerk card. A valid `next`
    // is kept; a missing or rejected one becomes /planning. Every other query
    // parameter (resume, reason, order, google...) is dropped: the retired
    // form was the only reader of those.
    // A plain URL, not request.nextUrl.clone(): Next 14.2's NextURL remembers
    // that the request path ended in "/" and re-appends it to href even after
    // the pathname is replaced, so /client-login/ would be rewritten to
    // /goaa-clerk-login/ (Round C1.7 run-all, reproduced on next 14.2.35).
    const target = new URL(request.nextUrl.href)
    target.pathname = CLERK_ENTRY_PATH
    target.search = ""
    target.searchParams.set("next", unifiedEntryNext(request.nextUrl.searchParams.get("next")))
    return withForwardedHeaders(
      NextResponse.rewrite(target),
      forwardHeaders(request, CLERK_ENTRY_MARKER_VALUE),
    )
  }

  return withForwardedHeaders(NextResponse.next(), forwardHeaders(request))
}

const clerkHandler = clerkMiddleware((_auth, request) => {
  const guarded = exposureGuard(request)
  if (guarded) return guarded
  return entryTransition(request)
})

function legacy(request: NextRequest): NextResponse {
  const guarded = exposureGuard(request)
  if (guarded) return guarded
  return NextResponse.next()
}

export default async function middleware(request: NextRequest, event: NextFetchEvent): Promise<Response> {
  const state = clerkAuthState()
  if (state === "disabled") return legacy(request)
  if (state === "misconfigured") return misconfigured(request)
  try {
    // The SDK types its result as possibly `undefined`; in practice our handler
    // always answers, and that response carries the auth headers Clerk set on
    // it. Only a genuinely empty result gets a plain pass-through.
    const result = await clerkHandler(request, event)
    return unifyLoopbackRewriteOrigin(result ?? NextResponse.next())
  } catch {
    return misconfigured(request)
  }
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:png|jpg|jpeg|svg|gif|webp|ico|css|js|map|woff2?)$).*)",
  ],
}
