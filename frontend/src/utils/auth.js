export function setSession({ user_id, role, nombre, token }) {
  if (user_id) localStorage.setItem('user_id', user_id)
  if (role) localStorage.setItem('user_role', role)
  if (nombre) localStorage.setItem('user_nombre', nombre)
  if (token) localStorage.setItem('auth_token', token)
}

export function clearSession() {
  localStorage.removeItem('user_id')
  localStorage.removeItem('user_role')
  localStorage.removeItem('user_nombre')
  localStorage.removeItem('auth_token')
}

export function getSession() {
  return {
    user_id: localStorage.getItem('user_id'),
    role: localStorage.getItem('user_role'),
    nombre: localStorage.getItem('user_nombre')
  }
}

export function getAuthToken() {
  return localStorage.getItem('auth_token')
}

export function authHeaders() {
  const t = getAuthToken()
  return t ? { Authorization: `Bearer ${t}` } : {}
}

export function getRole() {
  return localStorage.getItem('user_role')
}

export default { setSession, clearSession, getSession, getRole, getAuthToken, authHeaders }
