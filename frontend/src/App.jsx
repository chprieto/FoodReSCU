import { useEffect, useMemo, useState } from 'react'
import './App.css'
import SignIn from './components/SignIn'
import OrderCard from './components/OrderCard'
import { useNow, useOrders } from './hooks'
import { STATUS, uiStatus } from './orderStatus'

const USER_KEY = 'foodrescu.user'

const SECTIONS = [
  { status: STATUS.AVAILABLE, title: 'Available to claim', staffTitle: 'Available to students' },
  { status: STATUS.RESERVED, title: 'Reserved', staffTitle: 'Reserved' },
  { status: STATUS.UPCOMING, title: 'Coming soon', staffTitle: 'Not yet available (under 1h)' },
  { status: STATUS.PICKED_UP, title: 'Picked up', staffTitle: 'Picked up' },
  { status: STATUS.OLD, title: 'Expired', staffTitle: 'Expired (3h+)' },
]

function loadUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY))
  } catch {
    return null
  }
}

function Dashboard({ user, onSignOut }) {
  const now = useNow()
  const { orders, loading, refreshing, error, lastUpdated, nextRefreshAt, refresh } = useOrders(user)

  const grouped = useMemo(() => {
    const groups = Object.fromEntries(SECTIONS.map((s) => [s.status, []]))
    // The backend already limits what each role receives (students: claimable + their own).
    for (const order of orders) groups[uiStatus(order)].push(order)
    // newest first
    for (const list of Object.values(groups)) {
      list.sort((a, b) => new Date(b.time_made) - new Date(a.time_made))
    }
    return groups
  }, [orders])

  const visibleCount = Object.values(grouped).reduce((n, l) => n + l.length, 0)
  const isStaff = user.role === 'staff'
  const secondsLeft = nextRefreshAt ? Math.max(0, Math.ceil((nextRefreshAt - now) / 1000)) : null

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span aria-hidden="true">🥡</span> FoodReSCU
        </div>
        <div className="who">
          <span className="chip">{isStaff ? 'Staff' : `Student · ${user.studentId}`}</span>
          <button className="link" onClick={onSignOut}>Sign out</button>
        </div>
      </header>

      <main className="content">
        <div className="hero">
          <h1>{isStaff ? 'All orders' : 'Free food near you'}</h1>
          <p className="muted">
            {isStaff
              ? 'Every order, from fresh to expired.'
              : 'Orders left uncollected for an hour are free to claim. They expire after 3 hours.'}
          </p>
        </div>

        <div className="statusbar" aria-live="polite">
          <span className={`dot ${error ? 'bad' : 'ok'}`} />
          <span>
            {error
              ? 'Can’t reach the server — showing last known orders'
              : lastUpdated
                ? `Updated ${new Date(lastUpdated).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', second: '2-digit' })}`
                : 'Connecting…'}
            {secondsLeft !== null && !refreshing && ` · refreshing in ${secondsLeft}s`}
          </span>
          <button className="link" onClick={refresh} disabled={refreshing}>
            {refreshing ? 'Refreshing…' : 'Refresh now'}
          </button>
        </div>

        {error && <div className="banner">{error}</div>}

        {loading ? (
          <p className="empty">Loading orders…</p>
        ) : visibleCount === 0 ? (
          <div className="empty">
            <div className="empty-icon" aria-hidden="true">🍽️</div>
            <p>{isStaff ? 'No orders yet.' : 'Nothing to claim right now.'}</p>
            <p className="muted">This page checks for new food every 30 seconds.</p>
          </div>
        ) : (
          SECTIONS.map(({ status, title, staffTitle }) =>
            grouped[status].length === 0 ? null : (
              <section key={status} className="section">
                <h2>
                  {isStaff ? staffTitle : title}
                  <span className="count">{grouped[status].length}</span>
                </h2>
                <ul className="grid">
                  {grouped[status].map((order) => (
                    <OrderCard key={order.order_id} order={order} status={status} now={now} user={user} />
                  ))}
                </ul>
              </section>
            ),
          )
        )}
      </main>
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState(loadUser)

  useEffect(() => {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
    else localStorage.removeItem(USER_KEY)
  }, [user])

  return user ? <Dashboard user={user} onSignOut={() => setUser(null)} /> : <SignIn onSignIn={setUser} />
}
