// GOAA Gateway API Client
// ============================================================
// 2026-08-25: Contract v2 - frontend always calls GOAA Gateway
//   - no more createSession -> ws_url -> WebSocket
//   - POST /api/v1/chat directly, body: { user_id, message }
//   - read data.response
//   - model selection is decided by the backend Model Router (frontend is model-agnostic)
//   - Vercel preview redeploy trigger: no runtime behavior change.
//
// The frontend does not depend directly on QwenPaw / Ollama / any specific provider.
// ============================================================

const OPENCLAW_URL = process.env.NEXT_PUBLIC_OPENCLAW_URL ?? "https://api.goaa.ai"

export interface PlanStep {
  id: number
  title: string
  status: "active" | "completed" | "pending" | "blocked"
}

export interface PlanData {
  current_step: number
  steps: PlanStep[]
}

export interface ChatResult {
  sessionId: string
  stage: string
  intent: string | null
  domain: string | null
  subIntent: string | null
  displayTitle: string
  response: string
  knownFacts: Record<string, unknown>
  missingFields: string[]
  plan: PlanData
  confirmation: boolean
  connectionReady: boolean
  productAction: string | null
}

/**
 * GOAA Planning Flow v2 chat.
 * Subsequent requests in the same session must include sessionId (backend keeps conversation context).
 * The frontend does not infer domain / intent / stage / plan; it uses backend return values.
 */
export async function chat(userId: string, message: string, sessionId?: string): Promise<ChatResult> {
  const body: Record<string, string> = { user_id: userId, message }
  if (sessionId) body.session_id = sessionId

  const res = await fetch(`${OPENCLAW_URL}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new Error(`GOAA chat failed: ${res.status} ${text.slice(0, 120)}`)
  }

  const data = await res.json()
  if (data.status === "error") {
    throw new Error(data.message || "GOAA is temporarily unavailable. Please try again later.")
  }
  return {
    sessionId: data.session_id ?? "",
    stage: data.stage ?? "",
    intent: data.intent ?? null,
    domain: data.domain ?? null,
    subIntent: data.sub_intent ?? null,
    displayTitle: data.display_title ?? "GOAA Planning",
    response: data.response ?? "",
    knownFacts: data.known_facts ?? {},
    missingFields: data.missing_fields ?? [],
    plan: data.plan ?? { current_step: 1, steps: [] },
    confirmation: data.confirmation ?? false,
    connectionReady: data.connection_ready === true,
    productAction: typeof data.product_action === 'string' ? data.product_action : null,
  }
}

// ════════════════════════════════════════════════════════════
// [LEGACY] createSession / sendMessage - old WebSocket path
// Not the production default path; kept for future private provider / reference.
// New code should use chat().
// ════════════════════════════════════════════════════════════
export async function createSession(userId: string) {
  const res = await fetch(`${OPENCLAW_URL}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, content: "__init__" }),
  })

  if (!res.ok) {
    throw new Error(`createSession failed: ${res.status} ${res.statusText}`)
  }

  const data = await res.json()
  console.log('Session response:', data)

  return {
    sessionId: data.session_id,
    wsUrl: data.data?.ws_url ?? data.ws_url,
  }
}

export function sendMessage(wsUrl: string, content: string, timeoutMs = 60000): Promise<string> {
  return new Promise((resolve, reject) => {
    try {
      const ws = new WebSocket(wsUrl)

      const timer = setTimeout(() => {
        ws.close()
        reject(new Error("WebSocket timeout after " + timeoutMs + "ms"))
      }, timeoutMs)

      ws.onopen = () => {
        console.log('WebSocket connected')
        ws.send(JSON.stringify({ content, role: "user" }))
      }

      ws.onmessage = (event) => {
        clearTimeout(timer)
        console.log('WebSocket message received:', event.data)
        ws.close()

        try {
          const data = JSON.parse(event.data)
          const response = data.response ?? data.data?.response ?? JSON.stringify(data)
          resolve(response)
        } catch {
          resolve(event.data)
        }
      }

      ws.onerror = (error) => {
        clearTimeout(timer)
        console.error('WebSocket error:', error)
        reject(new Error("WebSocket error"))
      }

      ws.onclose = () => {
        console.log('WebSocket closed')
        clearTimeout(timer)
      }
    } catch (err) {
      reject(err)
    }
  })
}
