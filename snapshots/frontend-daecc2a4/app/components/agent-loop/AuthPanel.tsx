'use client'

/**
 * AuthPanel.tsx — sign in / create account for the isolated agent loop.
 *
 * The account created here is the SAME account that later applies for a
 * licence and becomes an agent. There is no second agent account and no second
 * credential. The session token never reaches the browser: the server-side BFF
 * stores it in an httpOnly cookie.
 */

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { api, ApiError } from '@/app/lib/agent-loop/api'

export default function AuthPanel() {
  const router = useRouter()
  const params = useSearchParams()
  const next = params.get('next') || '/agent-loop/customer'

  const [mode, setMode] = useState<'signin' | 'register'>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  async function onSignIn(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api.login({ email, password })
      router.push(next)
      router.refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'sign in failed')
      setBusy(false)
    }
  }

  async function onRegister(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await api.register({ email, password, full_name: fullName || undefined, phone: phone || undefined })
      // registering does not open a session — sign in with the same account
      await api.login({ email, password })
      setNotice('Account created and signed in.')
      router.push(next)
      router.refresh()
    } catch (err) {
      if (err instanceof ApiError && err.code === 'email_in_use') {
        setError('that e-mail already has an account — sign in instead')
      } else {
        setError(err instanceof ApiError ? err.message : 'registration failed')
      }
      setBusy(false)
    }
  }

  return (
    <div className="pp-root">
      <header className="pp-topbar">
        <div className="pp-brand">
          goaa.ai<span className="pp-brand-sub">Become an Agent</span>
        </div>
        <span className="pp-badge">C2 isolated · synthetic data</span>
      </header>
      <main className="pp-main" style={{ margin: '0 auto' }}>
        <div className="pp-panel" style={{ maxWidth: 520 }}>
          <div className="pp-tabs">
            <button
              type="button"
              className={`pp-tab${mode === 'signin' ? ' pp-active' : ''}`}
              data-testid="tab-signin"
              onClick={() => {
                setMode('signin')
                setError(null)
              }}
            >
              Sign in
            </button>
            <button
              type="button"
              className={`pp-tab${mode === 'register' ? ' pp-active' : ''}`}
              data-testid="tab-register"
              onClick={() => {
                setMode('register')
                setError(null)
              }}
            >
              Create account
            </button>
          </div>

          <h1 className="pp-h1">{mode === 'signin' ? 'Sign in to your account' : 'Create your account'}</h1>
          <p className="pp-body pp-muted">
            {mode === 'signin'
              ? 'Sign in with the account that owns (or will own) your licence application.'
              : 'Create an ordinary user account first. The licence application and any agent permission belong to this same account — there is no second account or second password.'}
          </p>

          {error ? (
            <p className="pp-err" data-testid="auth-error">
              {error}
            </p>
          ) : null}
          {notice ? <p className="pp-ok">{notice}</p> : null}

          <form onSubmit={mode === 'signin' ? onSignIn : onRegister}>
            <div className="pp-form-grid">
              <label className="pp-field">
                <span className="pp-inline-label">E-mail</span>
                <input
                  className="pp-input"
                  data-testid="auth-email"
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="synthetic.applicant@example.test"
                />
              </label>
              <label className="pp-field">
                <span className="pp-inline-label">Password</span>
                <input
                  className="pp-input"
                  data-testid="auth-password"
                  type="password"
                  autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
                  required
                  minLength={mode === 'register' ? 12 : undefined}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              {mode === 'register' ? (
                <>
                  <label className="pp-field">
                    <span className="pp-inline-label">Full name</span>
                    <input
                      className="pp-input"
                      data-testid="auth-full-name"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Synthetic Applicant"
                    />
                  </label>
                  <label className="pp-field">
                    <span className="pp-inline-label">Phone</span>
                    <input
                      className="pp-input"
                      data-testid="auth-phone"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+1 555 0100"
                    />
                  </label>
                </>
              ) : null}
            </div>

            <div className="pp-actions">
              <button className="pp-btn pp-btn-primary" data-testid="auth-submit" type="submit" disabled={busy}>
                {busy ? 'Working…' : mode === 'signin' ? 'Sign in' : 'Create account and sign in'}
              </button>
            </div>
            {mode === 'register' ? (
              <p className="pp-footnote">Passwords must be at least 12 characters (server-enforced).</p>
            ) : null}
          </form>
        </div>

        <p className="pp-footnote" style={{ maxWidth: 520 }}>
          This is the isolated C2 candidate environment. Use synthetic names, synthetic e-mail
          addresses and synthetic documents only. Nothing here is production.
        </p>
      </main>
    </div>
  )
}
