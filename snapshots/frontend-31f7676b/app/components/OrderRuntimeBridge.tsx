'use client'

import { useCallback, useEffect, useState } from 'react'
import { loadRuntimeOrder, runtimeOrderId, runtimeToken, RuntimeOrder } from '../lib/order-runtime'
import { OrderRole } from '../lib/order-api'

export function useOrderRuntime(role: OrderRole, refreshMs = 4000) {
  const [data, setData] = useState<RuntimeOrder | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    try {
      const next = await loadRuntimeOrder(runtimeOrderId(), runtimeToken(role))
      setData(next)
      setError('')
    } catch (err) {
      console.error('[order-runtime]', err)
      setError('Unable to refresh this order. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [role])

  useEffect(() => {
    refresh()
    const timer = window.setInterval(refresh, refreshMs)
    const storage = () => refresh()
    window.addEventListener('storage', storage)
    return () => {
      window.clearInterval(timer)
      window.removeEventListener('storage', storage)
    }
  }, [refresh, refreshMs])

  return { data, loading, error, refresh, orderId: runtimeOrderId(), token: runtimeToken(role) }
}

export function RuntimeBadge({ mode, loading, error }: { mode?: 'api'|'demo'; loading?: boolean; error?: string }) {
  const text = error ? 'Unable to refresh this order. Please try again.' : loading ? 'Syncing' : mode === 'api' ? 'Connected' : 'Preview'
  return <span title={error ? 'Unable to refresh this order. Please try again.' : ''} style={{fontSize:11,padding:'5px 8px',borderRadius:20,border:'1px solid #35303d',color:error?'#fca5a5':mode==='api'?'#86efac':'#aaa4b5',background:'#17151e'}}>{text}</span>
}
