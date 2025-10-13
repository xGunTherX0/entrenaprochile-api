export function setSession({ user_id, role, nombre }) {
  if (user_id) localStorage.setItem('user_id', user_id)
  if (role) localStorage.setItem('user_role', role)
  if (nombre) localStorage.setItem('user_nombre', nombre)
}

export function clearSession() {
  localStorage.removeItem('user_id')
  localStorage.removeItem('user_role')
  localStorage.removeItem('user_nombre')
}

export function getSession() {
  return {
    user_id: localStorage.getItem('user_id'),
    role: localStorage.getItem('user_role'),
    nombre: localStorage.getItem('user_nombre')
  }
}

export function getRole() {
  return localStorage.getItem('user_role')
}

export default { setSession, clearSession, getSession, getRole }
