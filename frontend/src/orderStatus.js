// Mirrors the rules in backend/app/order.py (ACTIVE_TIME / OLD_TIME).
// The backend owns the status of every order (it re-evaluates the 1h / 3h rules on each
// request), so the UI just maps it to a friendlier name. The constants below are only
// used for the "claim within..." countdowns.
export const ACTIVE_AFTER_MS = 60 * 60 * 1000 // 1 hour: students may claim it
export const OLD_AFTER_MS = 3 * 60 * 60 * 1000 // 3 hours: too old

export const STATUS = {
  UPCOMING: 'UPCOMING', // < 1h old, not yet claimable
  AVAILABLE: 'AVAILABLE', // 1h-3h old, up for grabs (backend: ACTIVE)
  RESERVED: 'RESERVED',
  PICKED_UP: 'PICKED_UP',
  OLD: 'OLD',
}

export function orderAgeMs(order, now) {
  return now - new Date(order.time_made).getTime()
}

export function uiStatus(order) {
  return order.status === 'ACTIVE' ? STATUS.AVAILABLE : (STATUS[order.status] ?? STATUS.UPCOMING)
}

export function formatDuration(ms) {
  const totalMin = Math.max(0, Math.floor(ms / 60_000))
  if (totalMin < 1) return 'under a minute'
  const h = Math.floor(totalMin / 60)
  const m = totalMin % 60
  if (h === 0) return `${m}m`
  return m === 0 ? `${h}h` : `${h}h ${m}m`
}
