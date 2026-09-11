/**
 * Clerk entry transition — shared helpers.
 *
 * Scope: this module only computes *where* a request should go and *whether*
 * the Clerk candidate is switched on. It never verifies a session and never
 * re-implements any part of the SDK: the trusted check lives in the official
 * `clerkMiddleware()` (middleware) and in the backend (`clerk-backend-api`).
 *
 * Switch semantics: `GOAA_C2_CLERK_AUTH_ENABLED` is the ONE switch, shared with
 * the backend. Missing or explicitly false -> legacy path, untouched. Enabled
 * but incompletely configured -> "misconfigured": the caller must refuse
 * through Clerk rather than quietly fall back to legacy, because a half
 * configured deployment is not a working deployment.
 */

export const UNIFIED_LOGIN_PATH = "/client-login"
/**
 * The internal sign-in page. It must NOT start with an underscore: Next.js
 * ignores any path segment prefixed with "_" (build/index.js,
 * server/dev/next-dev-server.js: `part.startsWith("_")`), so an
 * `app/__goaa/...` page is silently unroutable and a rewrite to it 404s.
 */
export const CLERK_ENTRY_PATH = "/goaa-clerk-login"
export const CLERK_ENTRY_MARKER = "x-goaa-clerk-entry"
export const CLERK_ENTRY_MARKER_VALUE = "middleware-rewrite"
/**
 * Default landing for the isolated test area. Every default this candidate
 * computes points inside `/agent-loop`, the test namespace: the golden
 * customer/agent destinations (`/client-dashboard/...`, `/agent-dashboard`)
 * are never produced by the transition.
 */
export const DEFAULT_AGENT_NEXT = "/agent-loop/customer"
export const AGENT_NEXT_PREFIX = "/agent-loop"
/**
 * The golden build's own, formal sign-in route. It is NOT an old alias: this
 * candidate never retires it, never redirects it and never rewrites it. The
 * isolated Clerk test entry is `/client-login`, and everything this candidate
 * defaults to lives under `/agent-loop` (see `AGENT_NEXT_PREFIX`), so a test
 * landing point can never become the golden customer/agent destination.
 */
export const GOLDEN_LOGIN_PATH = "/agent-login"
/**
 * The *test-only* sign-in alias. `/agent-login` is deliberately absent: it is
 * the golden product route, and treating it as a retired alias would replace a
 * real page's behaviour. Only the isolated `/agent-loop/*` namespace may be
 * redirected, and only to the one public entry point, `/client-login`.
 */
export const RETIRED_LOGIN_PATHS = ["/agent-loop/login"] as const
export const CLERK_SWITCH = "GOAA_C2_CLERK_AUTH_ENABLED"

export type ClerkAuthState = "disabled" | "enabled" | "misconfigured"

const TRUE_VALUES = ["1", "true", "yes", "on"]
const FALSE_VALUES = ["0", "false", "no", "off"]

type Env = Record<string, string | undefined>

function readEnv(name: string, env: Env): string {
  const value = env[name]
  return typeof value === "string" ? value.trim() : ""
}

/**
 * Three-state gate. An unreadable switch value is "misconfigured", never
 * "disabled": we only keep the legacy path when the switch says so explicitly.
 */
export function clerkAuthState(env: Env = process.env): ClerkAuthState {
  const raw = readEnv(CLERK_SWITCH, env).toLowerCase()
  if (raw === "" || FALSE_VALUES.includes(raw)) return "disabled"
  if (!TRUE_VALUES.includes(raw)) return "misconfigured"
  const publishable = readEnv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", env) || readEnv("CLERK_PUBLISHABLE_KEY", env)
  if (!publishable || !publishable.startsWith("pk_test_")) return "misconfigured"
  if (!readEnv("CLERK_SECRET_KEY", env)) return "misconfigured"
  return "enabled"
}

export function clerkMisconfiguredDetail(env: Env = process.env): string[] {
  const missing: string[] = []
  if (!readEnv(CLERK_SWITCH, env)) missing.push(CLERK_SWITCH)
  if (!(readEnv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", env) || readEnv("CLERK_PUBLISHABLE_KEY", env))) {
    missing.push("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
  }
  if (!readEnv("CLERK_SECRET_KEY", env)) missing.push("CLERK_SECRET_KEY")
  return missing
}

export type NextCheck = { ok: true; value: string } | { ok: false; reason: string }

const ENCODED_SEPARATOR = /%(2f|5c|00|0a|0d|09)/i
// The URL standard treats "%2e" as a dot segment, so `/a/%2e%2e/b` normalises to
// `/b` in the browser even though the text never contains "..". Refuse it too.
const ENCODED_DOT = /%(2e)/i
const SCHEME = /^[a-zA-Z][a-zA-Z0-9+.-]*:/

/**
 * Strict same-site check for a caller-supplied `next`.
 *
 * `next` is a *precondition* for the internal rewrite, never a value we repair
 * with a default: a missing or invalid value must leave the ordinary page
 * exactly as it is. Anything absolute, protocol-relative, backslashed,
 * control-bearing, percent-encoded, or outside the agent area is rejected.
 */
export function validateNextTarget(raw: unknown): NextCheck {
  if (typeof raw !== "string" || raw === "") return { ok: false, reason: "missing" }
  if (raw !== raw.trim()) return { ok: false, reason: "padded" }
  // eslint-disable-next-line no-control-regex
  if (/[\u0000-\u001f\u007f]/.test(raw)) return { ok: false, reason: "control-character" }
  if (raw.includes("\\")) return { ok: false, reason: "backslash" }
  if (ENCODED_SEPARATOR.test(raw)) return { ok: false, reason: "encoded-separator" }
  if (ENCODED_DOT.test(raw)) return { ok: false, reason: "encoded-dot-segment" }
  if (!raw.startsWith("/")) return { ok: false, reason: "not-root-relative" }
  if (raw.startsWith("//")) return { ok: false, reason: "protocol-relative" }
  if (SCHEME.test(raw)) return { ok: false, reason: "scheme" }
  if (raw.search(/[?#]/) !== -1) return { ok: false, reason: "query-or-fragment" }
  if (raw.split("/").some((segment) => segment === "." || segment === "..")) {
    return { ok: false, reason: "dot-segment" }
  }
  if (raw !== AGENT_NEXT_PREFIX && !raw.startsWith(`${AGENT_NEXT_PREFIX}/`)) {
    return { ok: false, reason: "outside-agent-loop" }
  }
  // Never bounce a sign-in straight back into a login entry: that is a loop.
  if ((RETIRED_LOGIN_PATHS as readonly string[]).includes(raw)) return { ok: false, reason: "login-loop" }
  if (raw === UNIFIED_LOGIN_PATH || raw === CLERK_ENTRY_PATH) return { ok: false, reason: "login-loop" }
  return { ok: true, value: raw }
}

/**
 * Post-authentication redirect target. Only ever used *after* the visitor is
 * signed in, so a missing value may fall back to the agent area; a supplied but
 * invalid one never can.
 */
export function safeNextTarget(raw: unknown): string {
  const checked = validateNextTarget(raw)
  return checked.ok ? checked.value : DEFAULT_AGENT_NEXT
}

export function isUnifiedLoginPath(pathname: string): boolean {
  return pathname === UNIFIED_LOGIN_PATH || pathname === `${UNIFIED_LOGIN_PATH}/`
}

export function trimTrailingSlash(pathname: string): string {
  if (pathname.length <= 1) return pathname
  return pathname.replace(/\/+$/, "")
}

/** Old sign-in entries: keep the link working with a server-side redirect. */
export function retiredEntryRedirect(pathname: string): string | null {
  const clean = trimTrailingSlash(pathname)
  if (!(RETIRED_LOGIN_PATHS as readonly string[]).includes(clean)) return null
  const query = new URLSearchParams({ next: DEFAULT_AGENT_NEXT })
  return `${UNIFIED_LOGIN_PATH}?${query.toString()}`
}

/** Paths the middleware must see. Kept here so tests can assert coverage. */
export const MATCHED_ENTRY_PATHS = [
  UNIFIED_LOGIN_PATH,
  CLERK_ENTRY_PATH,
  GOLDEN_LOGIN_PATH,
  RETIRED_LOGIN_PATHS[0],
  "/agent-loop/:path*",
  "/api/agent-loop/:path*",
] as const
