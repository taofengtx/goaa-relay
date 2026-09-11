// Visitor dismiss guard for /client-login (2026-09-05).
//
// Lets a visitor close the sign-in card and keep using the customer area
// WITHOUT authenticating. The dismiss path is a pure redirect:
//   - never creates login state (no client_token / client_username),
//   - never writes the goaa_signed_in cookie,
//   - never calls business write APIs,
//   - never touches localStorage.
//
// Same anti-open-redirect spirit as /client-logout (fixed enum destination).
// Instead of an enum we use an explicit allowlist compared on origin +
// pathname, so only same-origin /planning (any query/hash) and
// /client-dashboard (any existing subpath) are reachable. Anything else
// falls back to /planning.
//
// Pure functions only: no window, no storage, no cookie, no network.

export function isAllowedVisitorReturn(raw: string | null, baseOrigin: string): boolean {
  if (!raw || !baseOrigin) return false
  let parsed: URL
  try {
    parsed = new URL(raw, baseOrigin)
  } catch {
    return false
  }
  if (parsed.origin !== baseOrigin) return false
  const path = parsed.pathname
  if (path === "/planning") return true
  if (path === "/client-dashboard" || path.startsWith("/client-dashboard/")) return true
  return false
}

// Returns the safe destination to continue as a guest. The returned string is
// rebuilt from the parsed URL (pathname + search + hash) so query params like
// resume=1&reason=new-topic survive untouched while tricks like protocol-
// relative or encoded external URLs never reach window.location.
export function resolveVisitorDestination(raw: string | null, baseOrigin: string): string {
  if (!isAllowedVisitorReturn(raw, baseOrigin)) return "/planning"
  const parsed = new URL(raw as string, baseOrigin)
  return parsed.pathname + parsed.search + parsed.hash
}
