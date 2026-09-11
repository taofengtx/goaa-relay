'use client'

import { useEffect } from 'react'
import CustomerJourneyEntry from '../components/CustomerJourneyEntry'

const PENDING_PROMPT_KEY = 'goaa_pending_prompt_v1'

export default function PlanningPage() {
  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search)
    const prompt = searchParams.get('prompt')?.trim()
    if (!prompt) return

    window.localStorage.setItem(PENDING_PROMPT_KEY, prompt)
    window.history.replaceState(window.history.state, '', '/planning')
  }, [])

  return <CustomerJourneyEntry />
}
