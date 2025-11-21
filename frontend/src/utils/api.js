import auth from './auth.js'
import toast from './toast.js'
import router from '../router'

// In dev, prefer a relative base so Vite's dev-server proxy can handle `/api` requests
// If `VITE_API_BASE` is explicitly set, use it. Otherwise use '' in dev, and the
// production host for non-dev builds.
// In development we prefer a relative base so Vite's proxy handles /api requests
// even if a developer accidentally set VITE_API_BASE in a local .env file.
let BASE
if (import.meta.env.DEV) {
  // In development use a relative base so Vite's dev-server proxy handles `/api`.
  // This avoids CORS entirely while developing. Ensure you start Vite from the
  // `frontend` folder (so the proxy is active) with `npm run dev`.
  BASE = ''
} else {
  BASE = import.meta.env.VITE_API_BASE !== undefined
    ? import.meta.env.VITE_API_BASE
    : 'https://entrenaprochile-api.onrender.com'
}
// Normalize common shorthand values that developers sometimes set incorrectly
// e.g. ":5000" or "localhost:5000" -> ensure a full URL with scheme
try {
  if (typeof BASE === 'string') {
    const b = BASE.trim()
    // If BASE is intentionally empty (dev/proxy), keep it empty so relative
    // URLs are used and Vite proxy can intercept them.
    if (b === '') {
      BASE = ''
    } else if (b.startsWith(':')) {
      // ":5000" -> "http://localhost:5000"
      BASE = 'http://localhost' + b
    } else if (/^[0-9]+$/.test(b)) {
      // "5000" -> "http://localhost:5000"
      BASE = 'http://localhost:' + b
    } else if (!b.startsWith('http://') && !b.startsWith('https://')) {
      // "localhost:5000" -> "http://localhost:5000"
      BASE = 'http://' + b
    }
  }
} catch (e) {
  // fallback: keep original BASE
}
// Expose last network error for debug overlay
let lastNetworkError = null

function buildUrl(path) {
  if (!path) return BASE
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  return `${BASE}${path.startsWith('/') ? '' : '/'}${path}`
}

async function request(path, opts = {}) {
  const url = buildUrl(path)
  opts.headers = opts.headers || {}
  // Merge auth headers unless explicitly disabled
  if (!opts.skipAuth) {
    const ah = auth.authHeaders()
    opts.headers = { ...opts.headers, ...ah }
  }

  try {
    const res = await fetch(url, opts)
    // Only auto-redirect on auth errors when this request expected auth (skipAuth !== true).
    if (res && (res.status === 401 || res.status === 403) && !opts.skipAuth) {
      try { toast.show('No autorizado o sesión inválida — las acciones pueden fallar, por favor reintenta.', 4000) } catch (e) {}
    }
    lastNetworkError = null
    return res
  } catch (e) {
    // Record last network error for debug UI, and return a safe faux-response
    lastNetworkError = (e && e.message) ? e.message : String(e)
    try { toast.show('Error de red: ' + lastNetworkError, 4000) } catch (_) {}
    // Provide a Response-like object so callers using `res.ok` and `res.json()` don't throw
    return {
      ok: false,
      status: 0,
      json: async () => ({ error: 'network error', detail: lastNetworkError }),
      text: async () => lastNetworkError
    }
  }
}

export default {
  BASE,
  lastNetworkError: () => lastNetworkError,
  request,
  get: (path, opts = {}) => request(path, { ...opts, method: 'GET' }),
  post: (path, body, opts = {}) => request(path, { ...opts, method: 'POST', headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) }, body: JSON.stringify(body) }),
  put: (path, body, opts = {}) => request(path, { ...opts, method: 'PUT', headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) }, body: JSON.stringify(body) }),
  del: (path, opts = {}) => request(path, { ...opts, method: 'DELETE' })
}
