<template>
  <div class="min-h-screen flex bg-gray-50">
      <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Admin</h2>
      <ul>
        <li class="mb-2">
          <router-link to="/admin/usuarios" class="text-left w-full" :class="{'text-blue-600 font-semibold': activePanel==='usuarios'}">Gestionar Usuarios</router-link>
        </li>
        <li class="mb-2">
          <router-link to="/admin/aprobar" class="text-left w-full" :class="{'text-blue-600 font-semibold': activePanel==='aprobar'}">Aprobar Contenido</router-link>
        </li>
        <li class="mb-2">
          <router-link to="/admin/metricas" class="text-left w-full" :class="{'text-blue-600 font-semibold': activePanel==='metricas'}">Métricas</router-link>
        </li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>
      <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold">Admin Dashboard</h1>
      
      <!-- router outlet for admin child panels -->
      <div class="w-full">
        <router-view @refresh-metrics="loadMetrics"></router-view>
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
            <button @click="createUser" :disabled="creating" class="px-3 py-2 bg-blue-600 text-white rounded">{{ creating ? 'Creando...' : 'Crear' }}</button>
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
      createError: null
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
  methods: {
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
      if (!confirm('¿Eliminar usuario? Esta acción es irreversible.')) return
      try {
        const res = await api.del(`/api/admin/usuarios/${id}`)
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
