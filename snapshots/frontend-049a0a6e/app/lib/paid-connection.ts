/**
 * paid-connection.ts — launch switch for the $39.90 professional connection.
 *
 * At launch the golden order API (api.goaa.ai) is not changed and does not
 * accept the business credential that Clerk sign-in produces, so a signed-in
 * customer's purchase would fail at checkout. Until that API is updated the
 * purchase stays closed: the entry points show "coming soon" with the
 * 30-minute booking instead, and /connect-pass shows a notice instead of
 * mounting the checkout page (so it never calls the order API).
 *
 * Runtime, server-side switch (the root layout is dynamic): set
 *   GOAA_PAID_CONNECTION=open
 * in the service environment and restart to reopen; no rebuild. Anything else,
 * including unset, means closed.
 */
export const PAID_CONNECTION_SWITCH = "GOAA_PAID_CONNECTION"
export const BOOKING_URL = "https://cal.com/goaa.ai/30min"

type Env = Record<string, string | undefined>

export function paidConnectionOpen(env: Env = process.env): boolean {
  const raw = env[PAID_CONNECTION_SWITCH]
  return typeof raw === "string" && raw.trim().toLowerCase() === "open"
}
