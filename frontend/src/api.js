// Base URL of the FastAPI backend. Override with VITE_API_URL (see frontend/.env.example).
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// How often the UI asks the backend for a fresh copy of the orders.
export const POLL_INTERVAL_MS = 30_000

async function getJson(path, signal) {
  const res = await fetch(`${API_URL}${path}`, { signal })
  if (!res.ok) throw new Error(`Backend responded with ${res.status}`)
  return res.json()
}

async function postJson(path, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    // FastAPI puts the human-readable reason in `detail`.
    const err = await res.json().catch(() => null)
    throw new Error(typeof err?.detail === 'string' ? err.detail : `Backend responded with ${res.status}`)
  }
  return res.json()
}

/** Student reserves an available order. Sends the order id and who is asking. */
export function reserveOrder(orderId, studentId) {
  return postJson(`/orders/${orderId}/reserve`, { student_id: studentId })
}

/** Student marks their reserved order as picked up. */
export function pickUpOrder(orderId, studentId) {
  return postJson(`/orders/${orderId}/pickup`, { student_id: studentId })
}

/**
 * Fetches the orders this user is allowed to see, as one flat list.
 *
 *  - staff   -> GET /staff/orders   (every order, grouped by status)
 *  - student -> GET /student/orders (orders they can reserve + their own reservations)
 *
 * The backend filters by role, so students never receive other people's orders.
 */
export async function fetchOrders(user, signal) {
  if (user.role === 'staff') {
    const data = await getJson('/staff/orders', signal)
    return [
      ...data.upcoming,
      ...data.active,
      ...data.reserved,
      ...data.picked_up,
      ...data.old,
    ]
  }

  const data = await getJson(`/student/orders?student_id=${encodeURIComponent(user.studentId)}`, signal)
  return [...data.available, ...data.my_reservations, ...(data.my_picked_up ?? [])]
}
