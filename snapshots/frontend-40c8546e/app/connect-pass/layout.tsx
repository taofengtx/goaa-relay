import type { ReactNode } from "react"
import { BOOKING_URL, paidConnectionOpen } from "../lib/paid-connection"

// Decided per request from the runtime switch; never prerendered.
export const dynamic = "force-dynamic"

/**
 * While the paid connection is closed (see lib/paid-connection.ts) the
 * checkout page is not mounted at all, so none of its order-API calls run —
 * even for a visitor who arrives here from an old bookmark or a saved
 * sign-in return target. The page itself is unchanged.
 */
export default function ConnectPassLayout({ children }: { children: ReactNode }) {
  if (paidConnectionOpen()) return <>{children}</>
  return (
    <main data-testid="connect-pass-closed" style={{ minHeight: "100vh", background: "#0b0b10", color: "#fff", fontFamily: "system-ui,-apple-system,sans-serif", padding: "34px 18px 70px" }}>
      <div style={{ maxWidth: 560, margin: "12vh auto 0", display: "grid", gap: 14 }}>
        <h1 style={{ fontSize: 26, margin: 0 }}>Professional connection is opening soon</h1>
        <p style={{ color: "#b5b5bf", lineHeight: 1.7, margin: 0 }}>
          Paid connection to a licensed professional is not available yet, and nothing has been charged.
          You can book a 30-minute assessment with the GOAA team to plan your next step — booking never charges you.
        </p>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <a href={BOOKING_URL} target="_blank" rel="noopener noreferrer" style={{ padding: "11px 17px", borderRadius: 10, fontWeight: 650, background: "#6944cc", color: "#fff", textDecoration: "none" }}>Book a 30-minute assessment ↗</a>
          <a href="/planning" style={{ padding: "11px 17px", borderRadius: 10, fontWeight: 600, border: "1px solid rgba(255,255,255,.18)", color: "#fff", textDecoration: "none" }}>Back to AI Butler</a>
        </div>
      </div>
    </main>
  )
}
