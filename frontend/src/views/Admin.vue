<template>
  <div class="min-h-screen flex bg-gray-50">
    <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Admin</h2>
      <ul>
        <li class="mb-2"><a href="#" class="text-blue-600">Gestionar Usuarios</a></li>
        <li class="mb-2"><a href="#" class="text-blue-600">Aprobar Contenido</a></li>
        <li class="mb-2"><a href="#" class="text-blue-600">Métricas</a></li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>
    <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold">Admin Dashboard</h1>

      <section class="mt-6">
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

      <section class="mt-8">
        <h2 class="text-lg font-semibold">Usuarios</h2>
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
      loadingMetrics: false
    }
  },
  mounted() {
    this.loadUsers()
    this.loadMetrics()
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
    }
  }
}
</script>
