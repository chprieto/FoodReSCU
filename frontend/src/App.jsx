import { useEffect, useMemo, useState } from 'react'
import './App.css'
import SignIn from './components/SignIn'
import OrderCard from './components/OrderCard'
import { useNow, useOrders } from './hooks'
import { pickUpOrder, reserveOrder } from './api'
import { STATUS, uiStatus } from './orderStatus'

const USER_KEY = 'foodrescu.user'

// Students only: orders they reserved (and picked up), pinned above everything else.
const MINE = 'MINE'

const SECTIONS = [
  { status: MINE, title: 'Reserved by you', staffTitle: 'Reserved by you' },
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

  const [busyId, setBusyId] = useState(null)
  const [actionError, setActionError] = useState(null)

  // Sends the action to the backend with the order id + the signed-in student's id,
  // then reloads so the card moves to its new section.
  async function runAction(order, request) {
    setBusyId(order.order_id)
    setActionError(null)
    try {
      await request(order.order_id, user.studentId)
    } catch (err) {
      setActionError(err.message || 'Could not complete that action')
    } finally {
      setBusyId(null)
      refresh()
    }
  }
  const onReserve = (order) => runAction(order, reserveOrder)
  const onPickUp = (order) => runAction(order, pickUpOrder)

  const grouped = useMemo(() => {
    const groups = Object.fromEntries(SECTIONS.map((s) => [s.status, []]))
    // The backend already limits what each role receives (students: claimable + their own).
    for (const order of orders) {
      const status = uiStatus(order)
      const mine =
        user.role === 'student' &&
        order.reserved_by === user.studentId &&
        (status === STATUS.RESERVED || status === STATUS.PICKED_UP)
      groups[mine ? MINE : status].push(order)
    }
    // newest first
    for (const list of Object.values(groups)) {
      list.sort((a, b) => new Date(b.time_made) - new Date(a.time_made))
    }
    return groups
  }, [orders, user.role, user.studentId])

  const isStaff = user.role === 'staff'

  // Students get two pages: browse what can be claimed, and "My orders".
  const [tab, setTab] = useState('browse')
  const onMine = !isStaff && tab === 'mine'
  const pageSections = SECTIONS.filter((s) => (s.status === MINE ? onMine : !onMine))
  const visibleCount = pageSections.reduce((n, s) => n + grouped[s.status].length, 0)
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
          <h1>{isStaff ? 'All orders' : onMine ? 'My orders' : 'Free food near you'}</h1>
          <p className="muted">
            {isStaff
              ? 'Every order, from fresh to expired.'
              : onMine
                ? 'Food you’ve reserved. Mark it as picked up once you have it.'
                : 'Orders left uncollected for an hour are free to claim. They expire after 3 hours.'}
          </p>
        </div>

        {!isStaff && (
          <div className="segmented tabs" role="tablist" aria-label="Pages">
            {[
              ['browse', 'Available food'],
              ['mine', `My orders (${grouped[MINE].length})`],
            ].map(([key, label]) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={tab === key}
                className={tab === key ? 'on' : ''}
                onClick={() => setTab(key)}
              >
                {label}
              </button>
            ))}
          </div>
        )}

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
        {actionError && <div className="banner">{actionError}</div>}

        {loading ? (
          <p className="empty">Loading orders…</p>
        ) : visibleCount === 0 ? (
          <div className="empty">
            <div className="empty-icon" aria-hidden="true">🍽️</div>
            <p>{isStaff ? 'No orders yet.' : onMine ? 'You haven’t reserved anything yet.' : 'Nothing to claim right now.'}</p>
            <p className="muted">
              {onMine ? 'Reserve food from the “Available food” page.' : 'This page checks for new food every 30 seconds.'}
            </p>
          </div>
        ) : (
          pageSections.map(({ status, title, staffTitle }) =>
            grouped[status].length === 0 ? null : (
              <section key={status} className="section">
                <h2>
                  {isStaff ? staffTitle : title}
                  <span className="count">{grouped[status].length}</span>
                </h2>
                <ul className="grid">
                  {grouped[status].map((order) => (
                    <OrderCard
                      key={order.order_id}
                      order={order}
                      status={uiStatus(order)}
                      now={now}
                      user={user}
                      busy={busyId === order.order_id}
                      onReserve={onReserve}
                      onPickUp={onPickUp}
                    />
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
