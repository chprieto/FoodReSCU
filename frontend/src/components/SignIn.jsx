import { useState } from 'react'

// Placeholder sign-in: the backend has no auth endpoint yet, so this just
// records who is using the app. Swap for a real login call when one exists.
export default function SignIn({ onSignIn }) {
  const [role, setRole] = useState('student')
  const [studentId, setStudentId] = useState('')

  const canSubmit = role === 'staff' || studentId.trim().length > 0

  function submit(e) {
    e.preventDefault()
    if (!canSubmit) return
    onSignIn(
      role === 'staff'
        ? { role: 'staff' }
        : { role: 'student', studentId: studentId.trim() },
    )
  }

  return (
    <main className="signin">
      <form className="signin-card" onSubmit={submit}>
        <div className="logo" aria-hidden="true">🥡</div>
        <h1>FoodReSCU</h1>
        <p className="muted">Free leftover food, claimed before it goes to waste.</p>

        <div className="segmented" role="radiogroup" aria-label="I am a">
          {['student', 'staff'].map((r) => (
            <button
              key={r}
              type="button"
              role="radio"
              aria-checked={role === r}
              className={role === r ? 'on' : ''}
              onClick={() => setRole(r)}
            >
              {r === 'student' ? 'Student' : 'Staff'}
            </button>
          ))}
        </div>

        {role === 'student' && (
          <label className="field">
            <span>Student ID</span>
            <input
              autoFocus
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="e.g. 12345678"
            />
          </label>
        )}

        <button className="primary" type="submit" disabled={!canSubmit}>
          Continue
        </button>
      </form>
    </main>
  )
}
