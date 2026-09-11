/**
 * api.ts — browser-side client for the same-origin BFF.
 *
 * Every call goes to /api/agent-loop/* on this origin. No C2 host, port,
 * password, token or secret is written down here, and no token is ever put in
 * localStorage — the BFF keeps it in an httpOnly cookie.
 */

import { PUBLIC_PREFIX } from './shared'

export type SessionUser = {
  id: string
  email: string
  full_name: string | null
  phone: string | null
  email_verified: boolean
  roles: string[]
  created_at: string
}

export type ApplicationStatus =
  | 'draft'
  | 'submitted'
  | 'info_requested'
  | 'approved'
  | 'rejected'
  | 'suspended'

export type PreReview = {
  mode: string
  engine: string
  advisory: boolean
  can_auto_approve: boolean
  recommendation: string
  reasons: string[]
  missing_fields: string[]
  document_count: number
  license_count: number
  expired_licenses: number
}

export type License = {
  id: string
  license_type: string
  license_number: string
  issuer: string | null
  jurisdiction: string | null
  expires_on: string | null
  no_expiry: boolean
}

export type DocumentRow = {
  id: string
  side: string
  mime_type: string
  size_bytes: number
  sha256: string
  storage_label: string
  scan_status: string
  scanner: string
  ocr_mode: string
  uploaded_at: string
  own_view: boolean
}

export type Application = {
  id: string
  user_id: string
  status: ApplicationStatus
  full_name: string | null
  phone: string | null
  email: string | null
  address: string | null
  terms_accepted: boolean
  submitted_at: string | null
  decided_at: string | null
  decision_reason: string | null
  pre_review: PreReview | null
  created_at: string
  updated_at: string
  own_view: boolean
  licenses?: License[]
  documents?: DocumentRow[]
}

export type AuditEvent = {
  id: number
  action: string
  actor_role: string
  detail: Record<string, unknown> | null
  created_at: string
}

export class ApiError extends Error {
  status: number
  code: string
  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const target = PUBLIC_PREFIX + (path.startsWith('/') ? path : '/' + path)
  const res = await fetch(target, {
    ...init,
    cache: 'no-store',
    credentials: 'same-origin',
    headers: {
      accept: 'application/json',
      ...(init.body ? { 'content-type': 'application/json' } : {}),
      ...(init.headers || {}),
    },
  })
  const text = await res.text()
  let payload: unknown = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = null
    }
  }
  if (!res.ok) {
    const err = (payload as { error?: { code?: string; message?: string } } | null)?.error
    throw new ApiError(res.status, err?.code || 'request_failed', err?.message || `HTTP ${res.status}`)
  }
  return payload as T
}

export const api = {
  register(input: { email: string; password: string; full_name?: string; phone?: string }) {
    return request<{ user: SessionUser; next: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },
  login(input: { email: string; password: string }) {
    return request<{ user: SessionUser }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },
  logout() {
    return request<{ status: string }>('/auth/logout', { method: 'POST' })
  },
  me() {
    return request<{ user: SessionUser; application: { id: string; status: string } | null }>('/auth/me')
  },
  myApplication() {
    return request<{ application: Application }>('/applications/me')
  },
  saveDraft(input: {
    full_name?: string | null
    phone?: string | null
    email?: string | null
    address?: string | null
    terms_accepted: boolean
    licenses: Array<Omit<License, 'id'> & { id?: string }>
  }) {
    return request<{ application: Application }>('/applications/me', {
      method: 'PUT',
      body: JSON.stringify(input),
    })
  },
  submit() {
    return request<{ application: Application }>('/applications/me/submit', { method: 'POST' })
  },
  applicationById(id: string) {
    return request<{ application: Application }>(`/applications/${id}`)
  },
  async uploadDocument(file: File, side: string, licenseId?: string) {
    const res = await fetch(`${PUBLIC_PREFIX}/documents`, {
      method: 'POST',
      cache: 'no-store',
      credentials: 'same-origin',
      headers: {
        'content-type': file.type || 'application/octet-stream',
        'x-document-side': side,
        ...(licenseId ? { 'x-license-id': licenseId } : {}),
      },
      body: file,
    })
    const text = await res.text()
    const payload = text ? (JSON.parse(text) as { document?: DocumentRow; error?: { code: string; message: string } }) : {}
    if (!res.ok) throw new ApiError(res.status, payload.error?.code || 'upload_failed', payload.error?.message || `HTTP ${res.status}`)
    return payload as { document: DocumentRow }
  },
  /**
   * Same-origin URL that streams a licence document. The BFF exchanges the
   * short lived signed link server side, so no capability token is ever placed
   * in a browser visible URL, in HTML or in this bundle.
   */
  documentContentUrl(documentId: string) {
    return `${PUBLIC_PREFIX}/documents/${documentId}/content`
  },
  agentPanel() {
    return request<{ status: string; application_id: string; granted_at: string; licenses: License[] }>('/agent/panel')
  },
  adminQueue(status?: string) {
    const qs = status ? `?status=${encodeURIComponent(status)}` : ''
    return request<{ count: number; items: Application[] }>(`/admin/applications${qs}`)
  },
  adminDetail(id: string) {
    return request<{ application: Application; events: AuditEvent[] }>(`/admin/applications/${id}`)
  },
  adminDecide(id: string, action: 'approve' | 'reject' | 'request-info' | 'suspend', body: Record<string, unknown>, idempotencyKey: string) {
    return request<{ application: Application }>(`/admin/applications/${id}/${action}`, {
      method: 'POST',
      headers: { 'idempotency-key': idempotencyKey },
      body: JSON.stringify(body),
    })
  },
  adminRerunAi(id: string) {
    return request<{ application: Application }>(`/admin/applications/${id}/rerun-ai`, { method: 'POST' })
  },
}

export { PUBLIC_PREFIX }
