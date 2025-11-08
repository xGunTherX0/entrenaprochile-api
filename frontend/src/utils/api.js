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
    if (res && (res.status === 401 || res.status === 403)) {
      // Show toast and redirect to login
      try {
        toast.show('Sesión expirada o no autorizada. Redirigiendo al login...', 2000)
      } catch (e) {}
      try {
        auth.clearSession()
      } catch (e) {}
      // allow the toast to be visible briefly before navigating
      setTimeout(() => {
        try { router.push('/') } catch (e) { window.location.href = '/' }
      }, 1000)
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
