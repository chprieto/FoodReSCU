import { useState } from 'react'
import { login } from '../api'
import seal from '../assets/scu-seal.png'

// Students sign in with their student ID; staff with a staff ID and password.
// The backend validates both, and a bad login stops here with an error message.
export default function SignIn({ onSignIn }) {
  const [role, setRole] = useState('student')
  const [id, setId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const isStaff = role === 'staff'
  const canSubmit = id.trim().length > 0 && (!isStaff || password.length > 0) && !submitting

  function switchRole(next) {
    setRole(next)
    setId('')
    setPassword('')
    setError(null)
  }

  async function submit(e) {
    e.preventDefault()
    if (!canSubmit) return
    setSubmitting(true)
    setError(null)
    try {
      onSignIn(await login({ role, id: id.trim(), password }))
    } catch (err) {
      setError(err.message || 'Could not sign in')
      setSubmitting(false)
    }
  }

  return (
    <main className="signin">
      <form className="signin-card" onSubmit={submit}>
        <img className="seal" src={seal} alt="Santa Clara University seal" />
        <div className="signin-heading">
          <p className="eyebrow">Santa Clara University</p>
          <h1>Food<em>ReSCU</em></h1>
        </div>
        <p className="muted">Free leftover campus food, claimed before it goes to waste. Sign in to see what’s available.</p>

        <div className="segmented" role="radiogroup" aria-label="I am a">
          {['student', 'staff'].map((r) => (
            <button
              key={r}
              type="button"
              role="radio"
              aria-checked={role === r}
              className={role === r ? 'on' : ''}
              onClick={() => switchRole(r)}
            >
              {r === 'student' ? 'Student' : 'Staff'}
            </button>
          ))}
        </div>

        <label className="field">
          <span>{isStaff ? 'Staff ID' : 'Student ID'}</span>
          <input
            key={role}
            autoFocus
            value={id}
            onChange={(e) => {
              setId(e.target.value)
              setError(null)
            }}
            placeholder={isStaff ? 'e.g. STAFF001' : 'e.g. 12345678'}
            aria-invalid={error ? 'true' : undefined}
          />
        </label>

        {isStaff && (
          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                setError(null)
              }}
              autoComplete="current-password"
              aria-invalid={error ? 'true' : undefined}
            />
          </label>
        )}

        {error && (
          <div className="banner" role="alert">
            {error}
          </div>
        )}

        <button className="primary" type="submit" disabled={!canSubmit}>
          {submitting ? 'Signing in…' : 'Continue'}
        </button>
      </form>
    </main>
  )
}
