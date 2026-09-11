/**
 * shared.ts — constants safe to import from both the server and the browser.
 * Contains no token, secret or host credential.
 */

/** Prefix used by the FastAPI service (upstream). */
export const UPSTREAM_PREFIX = '/api/v1/agent-loop'

/** Public, same-origin prefix the browser talks to (the BFF). */
export const PUBLIC_PREFIX = '/api/agent-loop'

/** Rewrite an upstream-relative link into a same-origin BFF link. */
export function toPublicUrl(url: string): string {
  if (url.startsWith(UPSTREAM_PREFIX)) return PUBLIC_PREFIX + url.slice(UPSTREAM_PREFIX.length)
  return url
}
