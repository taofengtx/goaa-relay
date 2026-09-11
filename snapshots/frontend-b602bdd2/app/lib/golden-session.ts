/**
 * golden-session.ts — the browser half of the golden business-session bridge.
 *
 * WHY THIS EXISTS
 *   The golden (AI Butler) surface authenticates a customer with an opaque,
 *   database-backed, revocable business token. Clerk owns the *identity*; this
 *   module is how a Clerk-signed-in browser obtains the *business* credential
 *   without either system pretending to be the other.
 *
 * THE CONTRACT IT PRESERVES
 *   * The business credential stays the golden surface's own contract: an
 *     opaque token kept in `localStorage` under the key the golden surface
 *     already uses for a customer (`client_token`) and sent back as
 *     `Authorization: Bearer`. Only the server mints one, and only after it
 *     verified the Clerk session itself; this module stores it, gives it to
 *     nothing else, and deletes it on sign-out. `assertGoldenTokenShape()`
 *     refuses anything that is not the expected 32 hex shape, so a stray value
 *     cannot be persisted as if it were a credential.
 *   * It never sends an identity. No e-mail, user id, role, issuer or subject
 *     is passed anywhere: the API derives the identity from the Clerk session
 *     it verifies itself.
 *   * It never talks to a production origin. Every target is a same-origin
 *     relative path under `/api/agent-loop/`, checked by
 *     `assertTestOnlyTarget()` before any request is made.
 *   * It never reports a sign-out it could not confirm. If revocation cannot
 *     be proven, the caller gets `failed` and the caller must say so; the
 *     alternative — a cheerful message over a still-usable credential — is the
 *     bug this whole file is written to avoid.
 *
 * ORDER THAT MATTERS
 *   Business revocation runs *before* the Clerk sign-out, and it also works
 *   *after* one: `/golden/session/revoke` accepts the Clerk session when it is
 *   still valid and the business token itself when it is not. The second path
 *   is not a nicety — without it an out-of-order sign-out would leave a live
 *   credential behind, which is exactly the overlap that must not exist.
 *
 * ISOLATION NOTE
 *   Everything here is candidate-only code running against the isolated test
 *   stack (Next BFF 3102 → FastAPI 3103 → goaa_c2test). It writes no
 *   production data, and it issues no payment or order request.
 */

/** The one endpoint prefix this bridge is allowed to speak to. */
export const GOLDEN_SESSION_PATH = '/api/agent-loop/golden/session'

/** Where the browser records that this tab holds a business session. */
export const GOLDEN_SESSION_MARKER = 'goaa_golden_business_session'

/**
 * The key the golden (AI Butler) surface already uses for a customer's opaque
 * business credential. The bridge writes and deletes exactly this key, so the
 * golden business code keeps working against the contract it was built for.
 */
export const GOLDEN_CLIENT_TOKEN_KEY = 'client_token'

/** Only role this bridge may obtain in this round. */
export const GOLDEN_BUSINESS_ROLE = 'customer'

export const GOLDEN_SESSION_UNAVAILABLE =
  'The business session service is unreachable — please try again.'
export const GOLDEN_SIGN_OUT_FAILED =
  'Sign-out could not be confirmed: the business session may still be active. You have not been signed out.'

export class GoldenSessionError extends Error {
  readonly code: string

  constructor(code: string, message: string) {
    super(message)
    this.name = 'GoldenSessionError'
    this.code = code
  }
}

/* ------------------------------------------------------------------ target */

/**
 * True only for a same-origin relative path under the agent-loop BFF.
 *
 * A scheme of any kind is rejected, which is what keeps
 * `https://api.goaa.ai/...` — the golden surface's production order API — out
 * of reach even if a caller or an environment value somehow supplies it.
 * Protocol-relative (`//host`), backslash, parent segments, control characters
 * and whitespace are rejected too: none of them can be part of a relative path
 * to this origin, and accepting one would mean guessing what the browser does
 * with it.
 */
export function isTestOnlyTarget(target: unknown): target is string {
  if (typeof target !== 'string' || !target) return false
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(target)) return false
  if (target.startsWith('//')) return false
  if (target.includes('\\') || target.includes('..')) return false
  if (/[\s\u0000-\u001f]/.test(target)) return false
  if (target !== GOLDEN_SESSION_PATH && !target.startsWith(`${GOLDEN_SESSION_PATH}/`)) return false
  return true
}

export function assertTestOnlyTarget(target: unknown): string {
  if (!isTestOnlyTarget(target)) {
    throw new GoldenSessionError(
      'target_not_allowed',
      'the golden session bridge only talks to this origin\u2019s /api/agent-loop routes',
    )
  }
  return target
}

/* ------------------------------------------------------------- fetch shape */

export type GoldenFetch = (target: string, init?: RequestInit) => Promise<Response>

export type GoldenSession = { user_id: string; role: typeof GOLDEN_BUSINESS_ROLE }

/** The shape `GET /golden/session` answers with. */
export type GoldenSessionStatus =
  | { linked: false; session: null }
  | { linked: true; session: { user_id: string; role: string; live_tokens: number } }

/**
 * The shape of a golden business credential: 32 lowercase hex characters, the
 * same shape the business tier mints and looks up. Nothing else may be stored
 * in the golden credential slot: the value goes on to be sent as a Bearer
 * header, so accepting a token-shaped-looking string of unknown provenance
 * would be the same as accepting an unverified identity.
 */
export function assertGoldenTokenShape(token: unknown): string {
  if (typeof token !== 'string' || !/^[0-9a-f]{32}$/.test(token)) {
    throw new GoldenSessionError(
      'credential_malformed',
      'the server did not answer with a well-formed business credential',
    )
  }
  return token
}

/** Minimal `localStorage` surface; injected so tests never need a DOM. */
export type GoldenStorage = {
  getItem: (key: string) => string | null
  setItem: (key: string, value: string) => void
  removeItem: (key: string) => void
}

/** Store the credential under the golden key — the contract the golden UI reads. */
export function storeGoldenCredential(storage: GoldenStorage, token: string): void {
  storage.setItem(GOLDEN_CLIENT_TOKEN_KEY, assertGoldenTokenShape(token))
}

export function readGoldenCredential(storage: GoldenStorage): string | null {
  return storage.getItem(GOLDEN_CLIENT_TOKEN_KEY)
}

/** Delete the credential. Called on sign-out, and only then. */
export function clearGoldenCredential(storage: GoldenStorage): void {
  storage.removeItem(GOLDEN_CLIENT_TOKEN_KEY)
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

async function readJson(response: Response): Promise<Record<string, unknown>> {
  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }
  return asRecord(payload)
}

/**
 * The credential travels as a Bearer header — that is the golden contract.
 * Before a business credential exists (first sign-in of a tab, or after a
 * sign-out) the request carries none, and the server falls back to the Clerk
 * session it verifies itself.
 */
function authInit(credential: string | null): { headers?: Record<string, string> } {
  return credential ? { headers: { authorization: `Bearer ${credential}` } } : {}
}

/* ------------------------------------------------------------- operations */

/**
 * Is this tab's business session still accepted?
 *
 * `live` — the credential this browser holds (or the Clerk session, before a
 * business credential exists) resolves to a business principal, whose id is
 * echoed back (it is not a secret; it is the same id the
 * golden surface uses for the customer's matters and orders).
 * `absent` — no cookie, or the credential behind it is no longer accepted.
 * `unavailable` — the service could not be asked, so we do not know.
 *
 * This is a read. It never mints, rotates or extends anything, which is why a
 * page refresh preserves the session instead of replacing it.
 */
export async function checkBusinessSession(
  fetcher: GoldenFetch,
  credential: string | null = null,
): Promise<{ state: 'live'; session: GoldenSession } | { state: 'absent' } | { state: 'unavailable' }> {
  let response: Response
  try {
    response = await fetcher(assertTestOnlyTarget(`${GOLDEN_SESSION_PATH}/verify`), {
      method: 'GET',
      credentials: 'same-origin',
      cache: 'no-store',
      ...authInit(credential),
    })
  } catch {
    return { state: 'unavailable' }
  }
  if (response.status === 401 || response.status === 403 || response.status === 404) {
    return { state: 'absent' }
  }
  if (!response.ok) return { state: 'unavailable' }
  const payload = await readJson(response)
  const userId = typeof payload.user_id === 'string' ? payload.user_id : ''
  if (!userId) return { state: 'unavailable' }
  return { state: 'live', session: { user_id: userId, role: GOLDEN_BUSINESS_ROLE } }
}

/**
 * Ask the API to link this identity (once, by `(issuer, subject)`) and mint one
 * business credential. The credential comes back to this origin and goes
 * straight into the golden key — that is the slot the golden business code
 * reads. Only a well-formed credential is ever stored.
 */
export async function bootstrapBusinessSession(
  fetcher: GoldenFetch,
  storage: GoldenStorage | null = null,
): Promise<GoldenSession> {
  const response = await fetcher(assertTestOnlyTarget(GOLDEN_SESSION_PATH), {
    method: 'POST',
    credentials: 'same-origin',
    cache: 'no-store',
    headers: { 'content-type': 'application/json' },
    body: '{}',
  })
  if (!response.ok) {
    throw new GoldenSessionError(
      'bootstrap_failed',
      `the business session could not be started (HTTP ${response.status})`,
    )
  }
  const payload = await readJson(response)
  const userId = typeof payload.user_id === 'string' ? payload.user_id : ''
  const role = typeof payload.role === 'string' ? payload.role : ''
  if (!userId || role !== GOLDEN_BUSINESS_ROLE) {
    throw new GoldenSessionError(
      'bootstrap_invalid',
      'the business session response did not carry a customer principal',
    )
  }
  const token = assertGoldenTokenShape(payload.token)
  if (storage) storeGoldenCredential(storage, token)
  return { user_id: userId, role: GOLDEN_BUSINESS_ROLE }
}

/**
 * Start or resume the session, in the one order that is safe:
 *   1. check (a read) — on `live`, nothing is minted and nothing is rotated, so
 *      a refresh or a second tab does not invalidate what already works;
 *   2. only when the check says `absent` do we mint.
 * `unavailable` is reported, not papered over: minting into an unknown state
 * could rotate a credential that is still in use elsewhere.
 */
export async function startBusinessSession(
  fetcher: GoldenFetch,
  options: { credential?: string | null; storage?: GoldenStorage | null } = {},
): Promise<
  | { state: 'live'; session: GoldenSession; created: boolean }
  | { state: 'unavailable' }
  | { state: 'failed'; message: string }
> {
  const checked = await checkBusinessSession(fetcher, options.credential ?? null)
  if (checked.state === 'live') {
    return { state: 'live', session: checked.session, created: false }
  }
  if (checked.state === 'unavailable') return { state: 'unavailable' }
  try {
    const session = await bootstrapBusinessSession(fetcher, options.storage ?? null)
    return { state: 'live', session, created: true }
  } catch (error) {
    return {
      state: 'failed',
      message: error instanceof Error ? error.message : GOLDEN_SESSION_UNAVAILABLE,
    }
  }
}

/** What the API answers when a sign-out is requested. */
export type RevokeOutcome = { revoked: number; basis: 'clerk_session' | 'business_token' }

/**
 * Revoke every live business token for this identity.
 *
 * Sends no identity: only the credential this browser holds, as a Bearer
 * header — the business credential when there is one, and the Clerk session
 * (attached by the BFF) when the Clerk side is still alive. A non-2xx answer is
 * a failure, never a success.
 */
export async function revokeBusinessSession(
  fetcher: GoldenFetch,
  credential: string | null = null,
): Promise<RevokeOutcome> {
  const response = await fetcher(assertTestOnlyTarget(`${GOLDEN_SESSION_PATH}/revoke`), {
    method: 'POST',
    credentials: 'same-origin',
    cache: 'no-store',
    headers: { 'content-type': 'application/json', ...authInit(credential).headers },
    body: '{}',
  })
  if (!response.ok) {
    throw new GoldenSessionError(
      'revoke_failed',
      `the business session could not be revoked (HTTP ${response.status})`,
    )
  }
  const payload = await readJson(response)
  const revoked = typeof payload.revoked === 'number' ? payload.revoked : 0
  const basis = payload.basis === 'business_token' ? 'business_token' : 'clerk_session'
  return { revoked, basis }
}

/* --------------------------------------------------------------- sign-out */

export type EndSessionResult =
  | { status: 'ended'; revoked: number }
  | { status: 'not-started' }
  | { status: 'failed'; message: string }

/**
 * End the business session, in this order:
 *   1. revoke on the server, and require a confirmed answer;
 *   2. clear the browser-side marker.
 *
 * The marker is cleared only after the server confirmed. If revocation fails,
 * the marker stays and the caller is told `failed`: leaving a marker behind is
 * a visible inconsistency, whereas clearing it over a live credential would be
 * an invisible one.
 */
export async function endBusinessSession(deps: {
  fetch: GoldenFetch
  clearClient: () => void
  /** Whether this tab ever started a session; used for the 'not-started' case. */
  hadSession: boolean
  credential?: string | null
}): Promise<EndSessionResult> {
  const { fetch: fetcher, clearClient, hadSession, credential = null } = deps
  try {
    const outcome = await revokeBusinessSession(fetcher, credential)
    clearClient()
    return { status: 'ended', revoked: outcome.revoked }
  } catch (error) {
    if (error instanceof GoldenSessionError && error.code === 'revoke_failed' && !hadSession) {
      // Nothing was ever started in this tab and the server has no credential
      // for it: there is no session to end, and saying so is accurate.
      return { status: 'not-started' }
    }
    return {
      status: 'failed',
      message: error instanceof GoldenSessionError ? error.message : GOLDEN_SIGN_OUT_FAILED,
    }
  }
}

/**
 * The whole sign-out, with the business half gated on proof.
 *
 * Clerk's sign-out is the last step, never the first: if the business
 * revocation could not be confirmed we stop and report, because completing the
 * Clerk half would hide a business credential that is still usable.
 */
export async function signOutGoldenSession(deps: {
  fetch: GoldenFetch
  clearClient: () => void
  hadSession: boolean
  signOutClerk: () => Promise<void>
  credential?: string | null
}): Promise<EndSessionResult> {
  const ended = await endBusinessSession(deps)
  if (ended.status === 'failed') return ended
  await deps.signOutClerk()
  return ended
}

/* ------------------------------------------------------------- tab marker */

/** Read the per-tab marker. It carries a business id and a role — no secret. */
export function readMarker(storage: Pick<Storage, 'getItem'>): GoldenSession | null {
  const raw = storage.getItem(GOLDEN_SESSION_MARKER)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>
    if (typeof parsed.user_id !== 'string' || parsed.role !== GOLDEN_BUSINESS_ROLE) return null
    return { user_id: parsed.user_id, role: GOLDEN_BUSINESS_ROLE }
  } catch {
    return null
  }
}

export function writeMarker(storage: Pick<Storage, 'setItem'>, session: GoldenSession): void {
  storage.setItem(GOLDEN_SESSION_MARKER, JSON.stringify({ user_id: session.user_id, role: session.role }))
}

export function clearMarker(storage: Pick<Storage, 'removeItem'>): void {
  storage.removeItem(GOLDEN_SESSION_MARKER)
}
