// Customer sign-out session cleanup (2026-09-04).
//
// This module keeps its cleanup whitelist logic intentionally DOM-free and
// framework-free so the exact whitelist, nickname migration and "nothing else
// is touched" guarantees are unit-testable offline. It NEVER calls order /
// match / checkout / payment / account-delete APIs and never clears the whole
// storage. As a convenience the DOM-only mirror-flag cookie removal is
// invoked from clearCustomerSession (guarded no-op outside a browser / on
// non-goaa.ai hosts), keeping the three sign-out paths (account menu,
// /client-logout, any future reuse) consistent.
import { clearSignedInCookieFromDocument } from './goaa-cookie'
//
// Inventory source: app/client-login/page.tsx writes on successful customer
// login only client_token + client_username (plus goaa_active_order_id when
// the login URL carried ?order=...). The remaining keys below are the
// customer journey / order / pending-auth / handoff / checkout-attempt-lock /
// temp-state family that planning, connect-pass, customer-order-live and the
// personal-agent matter bridge read & write. Keys NOT in the whitelist stay
// untouched: goaa_planning_workspace_v1 (planning draft), butler nicknames,
// agent-role tokens, matter history/current matter views, demo state, other
// site preferences.

// Removed from window.localStorage by customer sign-out.
export const CLIENT_LOCAL_KEYS_TO_REMOVE: readonly string[] = [
  // customer token + identity display keys (login writes these; order-runtime
  // also accepts the legacy customer_token and the order-domain token)
  'client_token',
  'client_username',
  'customer_token',
  'goaa_order_customer_token',
  // current order id + customer journey
  'goaa_active_order_id',
  'goaa_customer_e2e_journey_v1',
  // pending purchase / auth return / auth reason / after-auth action
  'goaa_pending_purchase_v1',
  'goaa_auth_return_v1',
  'goaa_auth_reason_v1',
  'goaa_after_auth_action_v1',
  // temp states tied to the current login/order (pending prompt, handoff
  // package, matter→order links, checkout attempt lock residue)
  'goaa_pending_prompt_v1',
  'goaa_pending_professional_handoff_v1',
  'goaa_matter_order_links_v1',
  'goaa_connect_attempt_pending_v1',
] as const

// Removed from window.sessionStorage (checkout attempt lock lives there).
export const CLIENT_SESSION_KEYS_TO_REMOVE: readonly string[] = [
  'goaa_connect_attempt_pending_v1',
] as const

export const BUTLER_NICK_PREFIX = 'goaa_butler_display_name_v1:'
export const BUTLER_NICK_GUEST = `${BUTLER_NICK_PREFIX}guest`

export function butlerNickKeyFor(username: string): string {
  return `${BUTLER_NICK_PREFIX}${(username || 'guest').trim() || 'guest'}`
}

export interface StorageLike {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

export interface NicknameMigration {
  username: string
  sourceKey: string
  guestKey: string
  migratedValue: string | null
  keptExistingGuest: boolean
}

// Before identity keys are removed, migrate the signed-in user's butler
// nickname to the guest nickname key. Only the nickname VALUE is copied —
// never the username. If the guest key already has a value, that existing
// guest preference wins (we never clobber it).
export function migrateButlerNicknameToGuest(local: StorageLike): NicknameMigration {
  const username = local.getItem('client_username') || ''
  const sourceKey = butlerNickKeyFor(username)
  const guestKey = BUTLER_NICK_GUEST
  const currentNick = local.getItem(sourceKey)
  const existingGuest = local.getItem(guestKey)
  let migratedValue: string | null = null
  let keptExistingGuest = false
  if (currentNick && currentNick.trim()) {
    if (existingGuest && existingGuest.trim()) {
      keptExistingGuest = true
    } else {
      local.setItem(guestKey, currentNick)
      migratedValue = currentNick
    }
  }
  return { username, sourceKey, guestKey, migratedValue, keptExistingGuest }
}

// Single entry point used by the account menu. Migration happens first
// (while client_username is still readable), then the whitelisted keys are
// removed from localStorage and sessionStorage. Finally the cross-origin
// signed-in flag cookie is removed so the Framer homepage account menu no
// longer shows the signed-in state after sign-out.
export function clearCustomerSession(local: StorageLike, session: StorageLike): NicknameMigration {
  const migration = migrateButlerNicknameToGuest(local)
  for (const key of CLIENT_LOCAL_KEYS_TO_REMOVE) {
    try { local.removeItem(key) } catch { /* ignore single-key storage errors */ }
  }
  for (const key of CLIENT_SESSION_KEYS_TO_REMOVE) {
    try { session.removeItem(key) } catch { /* ignore single-key storage errors */ }
  }
  clearSignedInCookieFromDocument()
  return migration
}

export function isCustomerSignedIn(local: StorageLike): boolean {
  return Boolean(local.getItem('client_token'))
}

export function readCustomerOrderContext(local: StorageLike): { orderId: string | null; journey: unknown } {
  let journey: unknown = null
  try {
    const raw = local.getItem('goaa_customer_e2e_journey_v1')
    journey = raw ? JSON.parse(raw) : null
  } catch { journey = null }
  return { orderId: local.getItem('goaa_active_order_id'), journey }
}
