<template>
    <div class="min-h-screen flex bg-gray-100">
      <nav class="w-64 bg-indigo-700 text-white p-6 shadow-lg">
      <h2 class="text-xl font-bold mb-6 text-white">Admin</h2>
      <ul>
        <li class="mb-2">
          <router-link to="/admin/usuarios" class="text-left w-full block py-2 rounded" :class="{ 'bg-indigo-800/60 text-white font-semibold': activePanel==='usuarios', 'text-white/90 hover:text-white': activePanel!=='usuarios' }">Gestionar Usuarios</router-link>
        </li>
        <li class="mb-2">
          <router-link to="/admin/review" class="text-left w-full" :class="{'text-blue-600 font-semibold': activePanel==='review'}">Revisión Contenido</router-link>
        </li>
        <li class="mb-2">
          <router-link to="/admin/entrenadores" class="text-left w-full" :class="{'text-blue-600 font-semibold': activePanel==='entrenadores'}">Perfiles Entrenadores</router-link>
        </li>
        <li class="mb-2">
        </li>
        <!-- 'Aprobar Contenido' eliminado: la gestión se hace desde la vista de entrenador -->
        <li class="mb-2">
          <router-link to="/admin/metricas" class="text-left w-full block py-2 rounded" :class="{ 'bg-indigo-800/60 text-white font-semibold': activePanel==='metricas', 'text-white/90 hover:text-white': activePanel!=='metricas' }">Métricas</router-link>
        </li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 hover:bg-red-600 text-white rounded w-full">Cerrar Sesión</button>
      </div>
    </nav>
      <main class="flex-1 p-6">
      <div class="bg-white rounded-lg p-4 shadow-sm mb-6">
        <h1 class="text-2xl font-bold text-indigo-800">Admin Dashboard</h1>
        <p class="text-sm text-gray-600">Panel administrativo — gestiona usuarios, métricas y contenido.</p>
      </div>
      <!-- Network/offline banner: show when api reports a last network error -->
      <div v-if="lastNetworkError" class="mt-4 p-3 rounded bg-yellow-100 border-l-4 border-yellow-400 text-yellow-800">
        <div class="flex items-start justify-between">
          <div>
            <div class="font-semibold">Problema de red con el backend</div>
            <div class="text-sm">No se puede conectar con el servidor: intenta recargar o revisar que el backend esté corriendo.</div>
          </div>
          <div class="flex items-center space-x-2">
            <button @click="retryConnections" class="px-2 py-1 bg-blue-600 text-white rounded text-sm">Reintentar</button>
            <button @click="showNetworkDetails = !showNetworkDetails" class="px-2 py-1 border rounded text-sm">Detalles</button>
          </div>
        </div>
        <div v-if="showNetworkDetails" class="mt-2 text-xs font-mono whitespace-pre-wrap">{{ lastNetworkError }}</div>
      </div>

      <!-- router outlet for admin child panels -->
      <div class="w-full">
        <div class="bg-white rounded shadow-sm p-4 text-gray-800">
          <router-view @refresh-metrics="loadMetrics"></router-view>
        </div>
      </div>

      <!-- Create user modal -->
      <div v-if="showCreateModal" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40">
        <div class="bg-white rounded shadow-lg w-96 p-6">
          <h3 class="text-lg font-semibold mb-3">Crear Usuario</h3>
          <div class="mb-2">
            <label class="block text-sm">Email</label>
            <input v-model="newUser.email" class="w-full border rounded px-2 py-1" />
          </div>
          <div class="mb-2">
            <label class="block text-sm">Nombre</label>
            <input v-model="newUser.nombre" class="w-full border rounded px-2 py-1" />
          </div>
          <div class="mb-2">
            <label class="block text-sm">Password</label>
            <input type="password" v-model="newUser.password" class="w-full border rounded px-2 py-1" />
          </div>
          <div class="mb-4">
            <label class="block text-sm">Rol</label>
            <select v-model="newUser.role" class="w-full border rounded px-2 py-1">
              <option value="usuario">Usuario</option>
              <option value="cliente">Cliente</option>
              <option value="entrenador">Entrenador</option>
            </select>
          </div>
          <div class="flex justify-end">
            <button @click="closeModal" class="mr-2 px-3 py-2 border rounded">Cancelar</button>
            <button @click="createUser" :disabled="creating" class="px-3 py-2 bg-gradient-to-r from-indigo-600 to-blue-500 text-white rounded">{{ creating ? 'Creando...' : 'Crear' }}</button>
          </div>
          <div v-if="createError" class="mt-3 text-sm text-red-600">{{ createError }}</div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import auth from '../utils/auth.js'
import api from '../utils/api.js'

export default {
  name: 'Admin',
  data() {
    return {
      users: [],
      metrics: null,
      metricsError: null,
      error: null,
      loadingMetrics: false,
      // active panel: 'usuarios' | 'aprobar' | 'metricas'
      activePanel: 'usuarios',
      // create user modal state
      showCreateModal: false,
      newUser: { email: '', nombre: '', password: '', role: 'usuario' },
      creating: false,
      createError: null,
      // network banner state
      showNetworkDetails: false,
      networkRetryTimer: null
    }
  },
  computed: {
    lastNetworkError() {
      try { return api && typeof api.lastNetworkError === 'function' ? api.lastNetworkError() : null } catch(e) { return null }
    }
  },
  mounted() {
    // Initialize active panel from the route path (e.g. /admin/usuarios)
    const parts = (this.$route && this.$route.path) ? this.$route.path.split('/') : []
    const panel = parts[2] || 'usuarios'
    if (panel) this.activePanel = panel
    // Load data for the active panel
    if (this.activePanel === 'usuarios') this.loadUsers()
    if (this.activePanel === 'metricas') this.loadMetrics()

    // watch route changes (path) to react to navigation
    this.$watch(() => this.$route.path, (newPath) => {
      const p = (newPath || '').split('/')[2] || 'usuarios'
      if (p) this.select(p)
    })
  },
  // auto-retry watcher: start/stop interval when lastNetworkError toggles
  watch: {
    lastNetworkError(newVal) {
      // enable automatic retry only in dev/localhost to avoid production noise
      const hostname = (typeof window !== 'undefined' && window.location && window.location.hostname) ? window.location.hostname : ''
      const isLocalHost = ['localhost', '127.0.0.1', '::1'].includes(hostname)
      const isDevEnv = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.DEV) || isLocalHost
      if (newVal && isDevEnv) {
        if (!this.networkRetryTimer) {
          // retry every 10s
          this.networkRetryTimer = setInterval(() => {
            try { this.retryConnections() } catch (e) { /* swallow */ }
          }, 10000)
        }
      } else {
        if (this.networkRetryTimer) {
          clearInterval(this.networkRetryTimer)
          this.networkRetryTimer = null
        }
      }
    }
  },
  beforeUnmount() {
    if (this.networkRetryTimer) {
      clearInterval(this.networkRetryTimer)
      this.networkRetryTimer = null
    }
  },
  methods: {
    retryConnections() {
      // try to reload both panels; api wrapper will update its internal lastNetworkError
      if (this.activePanel === 'usuarios') this.loadUsers()
      if (this.activePanel === 'metricas') this.loadMetrics()
      // attempt both regardless
      this.loadUsers()
      this.loadMetrics()
      // hide details until there's something new
      this.showNetworkDetails = false
    },
    logout() {
      auth.clearSession()
      this.$router.push('/')
    },
    async loadUsers() {
      this.error = null
      try {
        const res = await api.get('/api/admin/usuarios')
        if (!res.ok) {
          const text = await res.json().catch(() => ({}))
          this.error = text.error || 'Error cargando usuarios'
          return
        }
        this.users = await res.json()
      } catch (e) {
        this.error = e.message || String(e)
      }
    },
    async loadMetrics() {
      this.metricsError = null
      this.loadingMetrics = true
      try {
        const res = await api.get('/api/admin/metrics')
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          console.error('Metrics error', res.status, body)
          this.metricsError = body.error || body.message || `Error cargando métricas (${res.status})`
          this.metrics = null
          return
        }
        this.metrics = await res.json()
      } catch (e) {
        console.error('Metrics fetch failed', e)
        this.metricsError = e.message || String(e)
        this.metrics = null
      } finally {
        this.loadingMetrics = false
      }
    },
    async promote(id) {
      this.error = null
      try {
        const res = await api.post(`/api/admin/usuarios/${id}/promote`, null)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || 'Error promoviendo usuario'
          return
        }
        await this.loadUsers()
        await this.loadMetrics()
      } catch (e) {
        this.error = e.message || String(e)
      }
    },
    select(panel) {
      // navigate to a real route so the URL reflects the selected panel
      try { this.$router.push(`/admin/${panel}`) } catch (e) {}
      this.activePanel = panel
      // lazy load panel data
      if (panel === 'usuarios') this.loadUsers()
      if (panel === 'metricas') this.loadMetrics()
    },
    async remove(id) {
      this.error = null
      // Ask admin whether to soft-disable (default) or hard-delete
      const soft = confirm('¿Deseas DESACTIVAR la cuenta en vez de eliminarla permanentemente?\nAceptar = Desactivar (recomendado), Cancelar = Eliminar permanentemente')
      if (!confirm('¿Confirmar la acción seleccionada?')) return
      const mode = soft ? 'soft' : 'hard'
      try {
        const res = await api.del(`/api/admin/usuarios/${id}?mode=${mode}`)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || 'Error borrando usuario'
          return
        }
        await this.loadUsers()
        await this.loadMetrics()
      } catch (e) {
        this.error = e.message || String(e)
      }
    },
    closeModal() {
      this.showCreateModal = false
      this.createError = null
      this.newUser = { email: '', nombre: '', password: '', role: 'usuario' }
      this.creating = false
    },
    async createUser() {
      this.createError = null
      if (!this.newUser.email || !this.newUser.password) {
        this.createError = 'Email y password son obligatorios'
        return
      }
      this.creating = true
      try {
        // Register endpoint (public) creates Usuario + Cliente by default
        const payload = { email: this.newUser.email, nombre: this.newUser.nombre || this.newUser.email, password: this.newUser.password }
        const res = await api.post('/api/usuarios/register', payload, { skipAuth: true })
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.createError = j.error || j.message || `Error creando usuario (${res.status})`
          return
        }
        const body = await res.json()
        const newId = body.id

        // If admin wants specific role, call admin endpoints to provision
        if (this.newUser.role === 'cliente') {
          const r2 = await api.post(`/api/admin/usuarios/${newId}/create_cliente`, null)
          if (!r2.ok) {
            const j2 = await r2.json().catch(() => ({}))
            this.createError = `Usuario creado pero fallo al crear cliente: ${j2.error || j2.detail || r2.status}`
          }
        } else if (this.newUser.role === 'entrenador') {
          const r3 = await api.post(`/api/admin/usuarios/${newId}/promote`, null)
          if (!r3.ok) {
            const j3 = await r3.json().catch(() => ({}))
            this.createError = `Usuario creado pero fallo al crear entrenador: ${j3.error || j3.detail || r3.status}`
          }
        }

        await this.loadUsers()
        await this.loadMetrics()
        // close if no createError, otherwise keep modal open to show message
        if (!this.createError) this.closeModal()
      } catch (e) {
        this.createError = e.message || String(e)
      } finally {
        this.creating = false
      }
    },
  }
}
</script>
