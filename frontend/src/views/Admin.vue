<template>
  <div class="min-h-screen flex bg-gray-50">
      <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Admin</h2>
      <ul>
        <li class="mb-2">
          <button @click="select('usuarios')" :class="{'text-blue-600 font-semibold': activePanel==='usuarios'}" class="text-left w-full">Gestionar Usuarios</button>
        </li>
        <li class="mb-2">
          <button @click="select('aprobar')" :class="{'text-blue-600 font-semibold': activePanel==='aprobar'}" class="text-left w-full">Aprobar Contenido</button>
        </li>
        <li class="mb-2">
          <button @click="select('metricas')" :class="{'text-blue-600 font-semibold': activePanel==='metricas'}" class="text-left w-full">Métricas</button>
        </li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>
      <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold">Admin Dashboard</h1>
      
      <!-- Panels: show only the active one -->
      <section v-if="activePanel === 'metricas'" class="mt-6">
        <h2 class="text-lg font-semibold">Métricas</h2>
        <div v-if="metrics" class="grid grid-cols-3 gap-4 mt-3">
          <div class="p-4 bg-white rounded shadow">
            <div class="text-sm text-gray-500">Usuarios</div>
            <div class="text-2xl font-bold">{{ metrics.total_users }}</div>
          </div>
          <div class="p-4 bg-white rounded shadow">
            <div class="text-sm text-gray-500">Clientes</div>
            <div class="text-2xl font-bold">{{ metrics.total_clientes }}</div>
          </div>
          <div class="p-4 bg-white rounded shadow">
            <div class="text-sm text-gray-500">Entrenadores</div>
            <div class="text-2xl font-bold">{{ metrics.total_entrenadores }}</div>
          </div>
        </div>
        <div v-else class="mt-3 text-sm text-gray-500">
          <div v-if="loadingMetrics">Cargando métricas...</div>
          <div v-else-if="metricsError" class="text-red-600">{{ metricsError }}</div>
          <div v-else class="text-gray-500">Cargando métricas...</div>
        </div>
      </section>

      <section v-if="activePanel === 'usuarios'" class="mt-8">
        <h2 class="text-lg font-semibold">Usuarios</h2>
        <div class="mt-3">
          <button @click="showCreateModal = true" class="px-3 py-2 bg-green-600 text-white rounded">Crear Usuario</button>
        </div>
        <div class="mt-3 bg-white rounded shadow overflow-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                <th class="px-6 py-3"></th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="u in users" :key="u.id">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ u.id }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ u.email }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ u.nombre }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ u.role }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button v-if="u.role !== 'entrenador' && u.role !== 'admin'" @click="promote(u.id)" class="text-indigo-600 hover:text-indigo-900 mr-3">Promover</button>
                  <button @click="remove(u.id)" class="text-red-600 hover:text-red-900">Borrar</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</div>
      </section>

      <section v-if="activePanel === 'aprobar'" class="mt-8">
        <h2 class="text-lg font-semibold">Aprobar Contenido</h2>
        <div class="mt-3 bg-white rounded shadow p-4">
          <p class="text-sm text-gray-600">Aquí puedes revisar y aprobar contenido enviado por usuarios. (Placeholder)</p>
          <div class="mt-3">
            <button class="px-3 py-2 bg-indigo-600 text-white rounded" @click.prevent="$router.push('/admin/aprobar')">Ir a aprobación (vista)</button>
          </div>
        </div>
      </section>

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

const API_BASE = import.meta.env.VITE_API_BASE || 'https://entrenaprochile-api.onrender.com'

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
    // Initialize active panel from URL hash if present
    const h = (this.$route && this.$route.hash) ? this.$route.hash.replace('#', '') : ''
    if (h) this.activePanel = h
    // Load data for the active panel
    if (this.activePanel === 'usuarios') this.loadUsers()
    if (this.activePanel === 'metricas') this.loadMetrics()

    // watch hash changes
    this.$watch(() => this.$route.hash, (newHash) => {
      const panel = (newHash || '').replace('#', '')
      if (panel) this.select(panel)
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
        const res = await fetch(`${API_BASE}/api/admin/usuarios`, { headers: auth.authHeaders() })
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
        const res = await fetch(`${API_BASE}/api/admin/metrics`, { headers: auth.authHeaders() })
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
        const res = await fetch(`${API_BASE}/api/admin/usuarios/${id}/promote`, { method: 'POST', headers: { ...auth.authHeaders(), 'Content-Type': 'application/json' } })
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
      // update URL hash so it's shareable
      try { this.$router.push({ path: this.$route.path, hash: `#${panel}` }) } catch (e) {}
      this.activePanel = panel
      // lazy load panel data
      if (panel === 'usuarios') this.loadUsers()
      if (panel === 'metricas') this.loadMetrics()
    },
    async remove(id) {
      this.error = null
      if (!confirm('¿Eliminar usuario? Esta acción es irreversible.')) return
      try {
        const res = await fetch(`${API_BASE}/api/admin/usuarios/${id}`, { method: 'DELETE', headers: auth.authHeaders() })
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
        const res = await fetch(`${API_BASE}/api/usuarios/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.createError = j.error || j.message || `Error creando usuario (${res.status})`
          return
        }
        const body = await res.json()
        const newId = body.id

        // If admin wants specific role, call admin endpoints to provision
        if (this.newUser.role === 'cliente') {
          const r2 = await fetch(`${API_BASE}/api/admin/usuarios/${newId}/create_cliente`, { method: 'POST', headers: auth.authHeaders() })
          if (!r2.ok) {
            const j2 = await r2.json().catch(() => ({}))
            this.createError = `Usuario creado pero fallo al crear cliente: ${j2.error || j2.detail || r2.status}`
          }
        } else if (this.newUser.role === 'entrenador') {
          const r3 = await fetch(`${API_BASE}/api/admin/usuarios/${newId}/promote`, { method: 'POST', headers: auth.authHeaders() })
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
