import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchOrders, POLL_INTERVAL_MS } from './api'

/** Current time, re-rendered every `stepMs`. Drives countdowns and the refresh timer. */
export function useNow(stepMs = 1000) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), stepMs)
    return () => clearInterval(id)
  }, [stepMs])
  return now
}

/**
 * Loads the orders visible to `user` from the backend and re-requests them every
 * `intervalMs`. Also refreshes when the tab becomes visible again (browsers throttle
 * timers in background tabs). On failure the last good data stays on screen.
 */
export function useOrders(user, intervalMs = POLL_INTERVAL_MS) {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [nextRefreshAt, setNextRefreshAt] = useState(null)
  const controllerRef = useRef(null)

  // Depend on primitives so a new-but-equal user object doesn't restart polling.
  const { role, studentId } = user

  const refresh = useCallback(async () => {
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller

    setRefreshing(true)
    try {
      const data = await fetchOrders({ role, studentId }, controller.signal)
      setOrders(data)
      setError(null)
      setLastUpdated(Date.now())
    } catch (err) {
      if (err.name === 'AbortError') return
      setError(err.message || 'Could not reach the server')
    } finally {
      if (controllerRef.current === controller) {
        setLoading(false)
        setRefreshing(false)
        setNextRefreshAt(Date.now() + intervalMs)
      }
    }
  }, [role, studentId, intervalMs])

  useEffect(() => {
    // Initial fetch syncs React with the external backend, which is what effects are for.
    // oxlint-disable-next-line react/set-state-in-effect
    refresh()
    const id = setInterval(refresh, intervalMs)
    const onVisible = () => document.visibilityState === 'visible' && refresh()
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      clearInterval(id)
      document.removeEventListener('visibilitychange', onVisible)
      controllerRef.current?.abort()
    }
  }, [refresh, intervalMs])

  return { orders, loading, refreshing, error, lastUpdated, nextRefreshAt, refresh }
}
