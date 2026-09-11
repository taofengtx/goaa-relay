'use client'

import { useEffect } from 'react'
import { CURRENT_MATTER_KEY, LEGACY_WORKSPACE_KEY, syncLegacyWorkspaceToCurrentMatter } from '../lib/personal-agent-matter'
import { KNOWLEDGE_VERIFICATION_EVENT } from '../lib/personal-agent-knowledge-verification'
import { trustedOwnerKnowledgeRecord } from '../lib/personal-agent-trusted-knowledge'

export const TRUSTED_KNOWLEDGE_RUNTIME_KEY = 'goaa_personal_agent_trusted_knowledge_v1'
export const TRUSTED_KNOWLEDGE_RUNTIME_EVENT = 'goaa:trusted-knowledge-ready'

// Transitional runtime bridge. The proven ChatComponent remains untouched.
// Matter state is mirrored into the Personal AI Agent model, while only
// owner-confirmed/owner-corrected knowledge is exposed as trusted long-term
// context for future Agent runtime integration.
export default function MatterRuntimeBridge() {
  useEffect(() => {
    let lastWorkspace = ''
    let lastTrusted = ''

    const syncTrustedKnowledge = () => {
      const trusted = JSON.stringify(trustedOwnerKnowledgeRecord())
      if (trusted === lastTrusted) return
      lastTrusted = trusted
      window.localStorage.setItem(TRUSTED_KNOWLEDGE_RUNTIME_KEY, trusted)
      window.dispatchEvent(new CustomEvent(TRUSTED_KNOWLEDGE_RUNTIME_EVENT))
    }

    const sync = () => {
      const workspace = window.localStorage.getItem(LEGACY_WORKSPACE_KEY) || ''
      if (workspace !== lastWorkspace) {
        lastWorkspace = workspace
        if (!workspace) window.localStorage.removeItem(CURRENT_MATTER_KEY)
        else syncLegacyWorkspaceToCurrentMatter()
      }
      syncTrustedKnowledge()
    }

    sync()
    const timer = window.setInterval(sync, 750)
    const handleVisibility = () => { if (document.visibilityState === 'visible') sync() }
    const handleVerification = () => syncTrustedKnowledge()

    document.addEventListener('visibilitychange', handleVisibility)
    window.addEventListener(KNOWLEDGE_VERIFICATION_EVENT, handleVerification)
    return () => {
      window.clearInterval(timer)
      document.removeEventListener('visibilitychange', handleVisibility)
      window.removeEventListener(KNOWLEDGE_VERIFICATION_EVENT, handleVerification)
    }
  }, [])

  return null
}
