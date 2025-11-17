<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Entrenadores</h1>
    <div v-if="loading" class="text-gray-500">Cargando entrenadores...</div>
    <div v-else>
      <div v-if="!trainers.length" class="text-gray-600">No se encontraron entrenadores.</div>
      <ul class="space-y-3">
        <li v-for="t in trainers" :key="t.usuario_id" class="border rounded p-3 bg-white flex justify-between items-center">
          <div>
            <div class="font-semibold text-lg">{{ t.nombre }}</div>
            <div class="text-sm text-gray-600">{{ t.speciality || 'Sin especialidad' }}</div>
            <div class="text-sm text-gray-500 mt-1">{{ t.bio ? (t.bio.length > 100 ? t.bio.slice(0,100) + '...' : t.bio) : '' }}</div>
          </div>
          <div>
            <router-link :to="{ name: 'EntrenadorPublico', params: { id: t.usuario_id } }" class="px-3 py-2 bg-blue-600 text-white rounded">Ver Perfil</router-link>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'
export default {
  name: 'ExplorarEntrenadores',
  data() {
    return {
      trainers: [],
      loading: false,
      error: null
    }
  },
  async created() {
    this.loading = true
    try {
      // Public endpoint: avoid sending Authorization header to prevent CORS preflight failures
  // use the safe public endpoint to avoid server 500 on the original route
  const res = await api.get('/api/public/entrenadores', { skipAuth: true })
      if (!res.ok) {
        const j = await res.json().catch(() => ({}))
        this.error = j.error || `Error cargando entrenadores (${res.status})`
        return
      }
      const j = await res.json()
      this.trainers = Array.isArray(j) ? j : []
    } catch (e) {
      this.error = e.message || String(e)
    } finally {
      this.loading = false
    }
  }
}
</script>
