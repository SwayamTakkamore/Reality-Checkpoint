// Thin fetch wrapper around the Reality Checkpoint FastAPI backend.
// Every call fails soft: the UI must never crash because the local model
// is cold, slow, or stopped.

const getApiBase = () => {
  const envUrl = import.meta.env.VITE_API_URL || ""
  if (!envUrl) return "/api"
  const trimmed = envUrl.replace(/\/+$/, "")
  return trimmed.endsWith("/api") ? trimmed : `${trimmed}/api`
}
const BASE = getApiBase()

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

async function request(path, { method = 'GET', body, signal } = {}) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    if (err?.name === 'AbortError') throw err
    throw new ApiError(
      'The checkpoint is offline. Is the backend running on port 8000?',
      0,
      null,
    )
  }

  const text = await res.text()
  let payload = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = { detail: text }
    }
  }

  if (!res.ok) {
    const detail = payload?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
          : `Request failed (${res.status})`
    throw new ApiError(message, res.status, payload)
  }

  return payload
}

export const api = {
  status: (opts) => request('/status', opts),

  player: (playerId = 'local-player', opts) =>
    request(`/player?player_id=${encodeURIComponent(playerId)}`, opts),

  storylines: (playerId = 'local-player', opts) =>
    request(`/storylines?player_id=${encodeURIComponent(playerId)}`, opts),

  generateQuest: (payload, opts) =>
    request('/quests/generate', { ...opts, method: 'POST', body: payload }),

  reflect: (payload, opts) =>
    request('/quests/reflect', { ...opts, method: 'POST', body: payload }),

  memories: ({ playerId = 'local-player', search, category, limit } = {}, opts) => {
    const qs = new URLSearchParams({ player_id: playerId })
    if (search) qs.set('search', search)
    if (category) qs.set('category', category)
    if (limit != null) qs.set('limit', String(limit))
    return request(`/memories?${qs.toString()}`, opts)
  },

  questHistory: (playerId = 'local-player', opts) =>
    request(`/quests?player_id=${encodeURIComponent(playerId)}`, opts),

  journal: (playerId = 'local-player', opts) =>
    request(`/journal/export?player_id=${encodeURIComponent(playerId)}`, opts),
}

// ---- Presentation helpers -------------------------------------------------

export const SENSORY_MODES = [
  { id: 'open', label: 'Open', hint: 'Let the checkpoint choose' },
  { id: 'visual', label: 'Visual', hint: 'Light, colour, contrast' },
  { id: 'auditory', label: 'Auditory', hint: 'Distance, layers, silence' },
  { id: 'tactile', label: 'Tactile', hint: 'Texture, temperature, weight' },
  { id: 'olfactory', label: 'Olfactory', hint: 'Air, thresholds, memory' },
  { id: 'kinetic', label: 'Kinetic', hint: 'Movement, rhythm, effort' },
]

export const TIME_BUDGETS = [5, 10, 15, 30]

export const MOODS = [
  'curious',
  'restless',
  'tired',
  'hopeful',
  'scattered',
  'quiet',
  'playful',
  'heavy',
]

export const STORYLINE_LABELS = {
  'architecture-of-shadows': 'Architecture of Shadows',
  'urban-biomecartography': 'Urban Biomecartography',
  'acoustic-commons': 'Acoustic Commons',
  'micro-physics': 'Micro-Physics',
  'ephemeral-encounters': 'Ephemeral Encounters',
}

export function storylineLabel(id) {
  if (!id) return ''
  return STORYLINE_LABELS[id] || id.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return '0s'
  const s = Math.floor(seconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h) return `${h}h ${m}m`
  if (m) return `${m}m ${sec}s`
  return `${sec}s`
}

export function formatClock(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds))
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

export function formatWhen(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function formatDay(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

// A stable per-browser player identity, so the journal survives reloads.
export function localPlayerId() {
  const KEY = 'reality-checkpoint.player'
  try {
    const existing = window.localStorage.getItem(KEY)
    if (existing) return existing
    const generated =
      'explorer-' +
      Math.random().toString(36).slice(2, 8) +
      Date.now().toString(36).slice(-4)
    window.localStorage.setItem(KEY, generated)
    return generated
  } catch {
    return 'local-player'
  }
}
