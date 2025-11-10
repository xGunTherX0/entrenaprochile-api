import auth from './auth.js'
import toast from './toast.js'
import router from '../router'

const BASE = import.meta.env.VITE_API_BASE || 'https://entrenaprochile-api.onrender.com'

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
    // If caller passed { skipAuth: true } we return the response so the caller can decide
    // how to handle 401/403 (for example when fetching a public resource).
    if (res && (res.status === 401 || res.status === 403) && !opts.skipAuth) {
      // Inform the user but DO NOT forcibly clear local session or redirect.
      // Automatic logout on any 401/403 caused accidental sign-outs (e.g. flaky
      // network, token verification race, or transient server issues). Keep
      // the token in localStorage so the user stays logged in and let UI
      // components handle failures per-request if they need to.
      try {
        toast.show('No autorizado o sesión inválida — las acciones pueden fallar, por favor reintenta. Si sigues teniendo problemas cierra sesión e inicia sesión nuevamente.', 4000)
      } catch (e) {}
      // Return the response so caller can decide what to do (show a modal,
      // attempt retry, or manually clear session). We deliberately avoid
      // calling auth.clearSession() or router.push('/') here.
    }
    return res
  } catch (e) {
    // rethrow for caller to handle network errors
    throw e
  }
}

export default {
  BASE,
  request,
  get: (path, opts = {}) => request(path, { ...opts, method: 'GET' }),
  post: (path, body, opts = {}) => request(path, { ...opts, method: 'POST', headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) }, body: JSON.stringify(body) }),
  put: (path, body, opts = {}) => request(path, { ...opts, method: 'PUT', headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) }, body: JSON.stringify(body) }),
  del: (path, opts = {}) => request(path, { ...opts, method: 'DELETE' })
}
