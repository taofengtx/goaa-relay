'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { orderApi, type OrderSummary } from '../lib/order-api'
import { readMatterHistory, restoreMatter, ensureMatterNumbers, type PersonalAgentMatter } from '../lib/personal-agent-matter'
import { buildButlerMatterRows, type MatterCategory } from '../lib/butler-matter-view'

type MatterFilter = 'all' | MatterCategory

const TABS: Array<{ key: MatterFilter; label: string }> = [
  { key: 'all', label: 'All' },
  { key: 'conversation', label: 'In Conversation' },
  { key: 'organizing', label: 'Organizing' },
  { key: 'connecting', label: 'Connecting' },
  { key: 'completed', label: 'Completed' },
]

export default function ButlerMattersView({ busy = false, onSignIn }: { busy?: boolean; onSignIn?: () => void }) {
  const [matters, setMatters] = useState<PersonalAgentMatter[]>([])
  const [orders, setOrders] = useState<OrderSummary[]>([])
  const [filter, setFilter] = useState<MatterFilter>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [signedIn, setSignedIn] = useState(false)
  const generation = useRef(0)

  const load = useCallback(async () => {
    const run = ++generation.current
    const token = window.localStorage.getItem('client_token')
    setMatters(ensureMatterNumbers(readMatterHistory()))
    setOrders([])
    setSignedIn(Boolean(token))
    setLoading(Boolean(token))
    setError('')
    if (!token) return
    const current = () => generation.current === run && window.localStorage.getItem('client_token') === token
    try {
      const result = await orderApi.listOrders(token)
      if (!current()) return
      const ids = [...new Set(result.orders.map(item => typeof item.id === 'string' ? item.id : '').filter(Boolean))]
      const details: OrderSummary[] = []
      let unavailable = 0
      for (let i = 0; i < ids.length && current(); i += 4) {
        const batch = await Promise.all(ids.slice(i, i + 4).map(id => orderApi.getOrder(id, token).catch(() => null)))
        for (const item of batch) { if (item) details.push(item); else unavailable += 1 }
      }
      if (!current()) return
      setOrders(details)
      if (unavailable) setError('Some orders could not be loaded right now; the list may be incomplete. Please refresh later.')
    } catch {
      if (current()) setError('Unable to load orders right now. Your local planning records are still here; order status was not inferred.')
    } finally {
      if (current()) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
    const onStorage = (event: StorageEvent) => {
      if (event.key === 'client_token' || event.key === null) void load()
      else setMatters(readMatterHistory())
    }
    window.addEventListener('storage', onStorage)
    return () => { generation.current += 1; window.removeEventListener('storage', onStorage) }
  }, [load])

  const rows = buildButlerMatterRows(matters, orders)
  const counts = {
    all: rows.length,
    conversation: 0,
    organizing: 0,
    connecting: 0,
    completed: 0,
  }
  for (const row of rows) counts[row.category] += 1
  const visible = filter === 'all' ? rows : rows.filter(item => item.category === filter)

  function resume(id: string) {
    if (busy) return
    if (!restoreMatter(id)) { setError('This planning record could not be restored. Please refresh the list.'); return }
    // ChatComponent consumes the established restore event in-place; no prompt replay.
  }

  return <section className="butler-matters" aria-labelledby="butler-matters-title">
    <div className="butler-view-heading"><div><span className="workspace-kicker">MY MATTERS</span><h2 id="butler-matters-title">Matters</h2><p>Check progress, continue the conversation, or review what&apos;s done.</p></div><button type="button" className="butler-secondary" onClick={() => void load()} disabled={loading}>Refresh</button></div>
    <div className="butler-filters" aria-label="Matter status">
      {TABS.map(tab => <button key={tab.key} type="button" aria-pressed={filter === tab.key} onClick={() => setFilter(tab.key)}>{tab.label} <span>{counts[tab.key]}</span></button>)}
    </div>
    {!signedIn && <p className="butler-notice">Showing local planning records.<a href="/client-login" onClick={onSignIn ? event => { event.preventDefault(); if (!busy) onSignIn() } : undefined}>Sign in</a> to load your professional service orders.</p>}
    {loading && <p role="status" className="butler-notice">Loading your service orders…</p>}
    {error && <p role="alert" className="butler-notice">{error}</p>}
    {busy && <p role="status" className="butler-notice">The butler is replying. Switch matters when it finishes to avoid interrupting the current conversation.</p>}
    <div className="butler-matter-list">
      {visible.map(row => <article key={row.id} className="butler-matter-card">
        <div className="butler-matter-heading"><h3>{row.matter && typeof row.matter.number === 'number' ? `#${row.matter.number} ${row.title}` : row.title}</h3><span className={`butler-state ${row.group}`}>{row.status}</span></div>
        <p className="butler-matter-meta">{row.order ? 'Professional service order' : 'Local planning record'}{row.updatedAt && <> · {new Date(row.updatedAt).toLocaleDateString()}</>}</p>
        <div className="butler-matter-actions">
          {row.order && <a className="butler-primary" href={`/customer-order-live?order=${encodeURIComponent(row.order.id)}`}>{row.category === 'completed' ? 'View results' : 'View details'}</a>}
          {row.order?.invoice && <a className="butler-secondary" href={`/customer-order-live?order=${encodeURIComponent(row.order.id)}`}>View invoice</a>}
          {row.matter && <button type="button" className="butler-secondary" disabled={busy} onClick={() => resume(row.matter!.id)}>Continue with Butler</button>}
        </div>
        {row.order && <p className="butler-matter-note">Open the order workspace to view butler collaboration, supplements, and delivery records.</p>}
      </article>)}
    </div>
    {!loading && !visible.length && <div className="butler-empty"><h3>{filter === 'completed' ? 'No completed matters yet' : 'No matters in this stage'}</h3><p>{error ? 'Order loading was incomplete. Please refresh later.' : filter === 'completed' ? 'Professional service orders you confirm as done will appear here.' : 'Tell the butler what you need in chat to get started.'}</p></div>}
  </section>
}
