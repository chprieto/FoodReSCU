import {
  ACTIVE_AFTER_MS,
  OLD_AFTER_MS,
  STATUS,
  formatDuration,
  orderAgeMs,
} from '../orderStatus'

const BADGE = {
  [STATUS.AVAILABLE]: { label: 'Available', tone: 'green' },
  [STATUS.UPCOMING]: { label: 'Not yet available', tone: 'blue' },
  [STATUS.RESERVED]: { label: 'Reserved', tone: 'amber' },
  [STATUS.PICKED_UP]: { label: 'Picked up', tone: 'gray' },
  [STATUS.OLD]: { label: 'Expired', tone: 'red' },
}

function detail(order, status, now) {
  const age = orderAgeMs(order, now)
  switch (status) {
    case STATUS.AVAILABLE:
      return `Claim within ${formatDuration(OLD_AFTER_MS - age)}`
    case STATUS.UPCOMING:
      return `Opens to students in ${formatDuration(ACTIVE_AFTER_MS - age)}`
    case STATUS.RESERVED:
      return `Reserved ${formatDuration(now - new Date(order.time_reserved ?? order.time_made))} ago`
    case STATUS.PICKED_UP:
      return 'Enjoy your meal!'
    default:
      return `Out for ${formatDuration(age)}`
  }
}

export default function OrderCard({ order, status, now, user, busy, onReserve, onPickUp }) {
  const badge = BADGE[status]
  const isStudent = user.role === 'student'
  const mine = isStudent && order.reserved_by === user.studentId

  return (
    <li className={`card ${status.toLowerCase()}`}>
      <div className="card-top">
        <h3>{order.item}</h3>
        <span className={`badge ${badge.tone}`}>{mine && status !== STATUS.OLD ? 'Yours' : badge.label}</span>
      </div>
      <p className="detail">{detail(order, status, now)}</p>
      <p className="meta">
        Made {formatDuration(orderAgeMs(order, now))} ago
        {user.role === 'staff' && order.reserved_by && <> · reserved by {order.reserved_by}</>}
      </p>
      {isStudent && status === STATUS.AVAILABLE && (
        <button className="primary card-action" disabled={busy} onClick={() => onReserve(order)}>
          {busy ? 'Reserving…' : 'Reserve'}
        </button>
      )}
      {mine && status === STATUS.RESERVED && (
        <button className="primary card-action" disabled={busy} onClick={() => onPickUp(order)}>
          {busy ? 'Saving…' : 'Mark as picked up'}
        </button>
      )}
    </li>
  )
}
