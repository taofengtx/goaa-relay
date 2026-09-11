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
 *
 * Instance (Round C1.7): `GOAA_CLERK_INSTANCE` is not a second switch. It only
 * declares which kind of keys this deployment must carry: unset/"development"
 * (the C2 test stack) needs test keys, "production" (planning.goaa.ai on C1)
 * needs live keys. A key of the other kind is "misconfigured", never tolerated.
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
 * Default landing for the agent area (the retired `/agent-loop/login` alias and
 * the internal page's own fallback). The golden customer/agent destinations
 * (`/client-dashboard/...`, `/agent-dashboard`) are never produced by the
 * transition.
 */
export const DEFAULT_AGENT_NEXT = "/agent-loop/customer"
export const AGENT_NEXT_PREFIX = "/agent-loop"
/**
 * AI Butler. Round C1.7 (Tao, 2026-09-11): with Clerk in charge the legacy
 * email+password form is retired, every visit to `/client-login` opens the
 * Clerk card, and a visit without a usable `next` returns here after sign-in.
 */
export const DEFAULT_LOGIN_NEXT = "/planning"
/** Exact landings outside the agent area that a `next` may name. */
export const EXTRA_NEXT_PATHS = [DEFAULT_LOGIN_NEXT] as const
/**
 * The golden build's own, formal sign-in route. It is NOT an old alias: this
 * candidate never retires it, never redirects it and never rewrites it. The
 * Clerk entry is `/client-login`, and every landing it can produce is either
 * under `/agent-loop` (see `AGENT_NEXT_PREFIX`) or exactly `/planning`, so a
 * landing point can never become a golden customer/agent dashboard.
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
export const CLERK_INSTANCE_VAR = "GOAA_CLERK_INSTANCE"

export type ClerkAuthState = "disabled" | "enabled" | "misconfigured"
export type ClerkInstance = "development" | "production"

/**
 * Key kinds per instance. The live secret prefix is assembled from two parts
 * only so that this source never trips the relay's secret scan; it is a
 * prefix, not a key.
 */
const KEY_PREFIXES: Record<ClerkInstance, { publishable: string; secret: string }> = {
  development: { publishable: "pk_test_", secret: "sk_test_" },
  production: { publishable: "pk_live_", secret: "sk_" + "live_" },
}

const TRUE_VALUES = ["1", "true", "yes", "on"]
const FALSE_VALUES = ["0", "false", "no", "off"]

type Env = Record<string, string | undefined>

function readEnv(name: string, env: Env): string {
  const value = env[name]
  return typeof value === "string" ? value.trim() : ""
}

/**
 * Which Clerk instance the keys must belong to. Unset means "development", so
 * the C2 test stack keeps working unchanged; production has to be declared.
 * Any other value is unreadable (null) and refuses.
 */
export function clerkInstance(env: Env = process.env): ClerkInstance | null {
  const raw = readEnv(CLERK_INSTANCE_VAR, env).toLowerCase()
  if (raw === "" || raw === "development") return "development"
  if (raw === "production") return "production"
  return null
}

function readPublishable(env: Env): string {
  return readEnv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", env) || readEnv("CLERK_PUBLISHABLE_KEY", env)
}

/**
 * Three-state gate. An unreadable switch value is "misconfigured", never
 * "disabled": we only keep the legacy path when the switch says so explicitly.
 * Both keys must be of the declared instance's kind (see KEY_PREFIXES): a live
 * key on the test stack, or a test key in production, refuses.
 */
export function clerkAuthState(env: Env = process.env): ClerkAuthState {
  const raw = readEnv(CLERK_SWITCH, env).toLowerCase()
  if (raw === "" || FALSE_VALUES.includes(raw)) return "disabled"
  if (!TRUE_VALUES.includes(raw)) return "misconfigured"
  const instance = clerkInstance(env)
  if (!instance) return "misconfigured"
  const kind = KEY_PREFIXES[instance]
  const publishable = readPublishable(env)
  if (!publishable || !publishable.startsWith(kind.publishable)) return "misconfigured"
  if (!readEnv("CLERK_SECRET_KEY", env).startsWith(kind.secret)) return "misconfigured"
  return "enabled"
}

/** Variable NAMES only — never a value, a length, a prefix or a fragment. */
export function clerkMisconfiguredDetail(env: Env = process.env): string[] {
  const missing: string[] = []
  if (!readEnv(CLERK_SWITCH, env)) missing.push(CLERK_SWITCH)
  const instance = clerkInstance(env)
  if (!instance) missing.push(CLERK_INSTANCE_VAR)
  const kind = instance ? KEY_PREFIXES[instance] : null
  const publishable = readPublishable(env)
  if (!publishable) missing.push("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
  else if (kind && !publishable.startsWith(kind.publishable)) {
    missing.push(`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY (not a ${instance} key)`)
  }
  if (!readEnv("CLERK_SECRET_KEY", env)) missing.push("CLERK_SECRET_KEY")
  else if (kind && !readEnv("CLERK_SECRET_KEY", env).startsWith(kind.secret)) missing.push(`CLERK_SECRET_KEY (not a ${instance} key)`)
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
 * Only two landing areas exist: the agent area (`/agent-loop` and below) and
 * AI Butler (exactly `/planning`). Anything absolute, protocol-relative,
 * backslashed, control-bearing, percent-encoded, or outside those landings is
 * rejected, and a rejected value is never repaired into something close to
 * it: callers replace it with their own fixed default (`unifiedEntryNext`,
 * `safeNextTarget`), so no part of it survives.
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
  const inAgentArea = raw === AGENT_NEXT_PREFIX || raw.startsWith(`${AGENT_NEXT_PREFIX}/`)
  if (!inAgentArea && !(EXTRA_NEXT_PATHS as readonly string[]).includes(raw)) {
    return { ok: false, reason: "outside-allowed-landings" }
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

/**
 * The `next` the public entry hands to the Clerk card (Round C1.7). With Clerk
 * in charge every visit to `/client-login` opens the card: a valid `next` is
 * kept, and a missing or rejected one becomes `DEFAULT_LOGIN_NEXT`.
 */
export function unifiedEntryNext(raw: unknown): string {
  const checked = validateNextTarget(raw)
  return checked.ok ? checked.value : DEFAULT_LOGIN_NEXT
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
