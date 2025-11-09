<template>
  <div class="p-6">
    <button @click="$router.back()" class="mb-4 px-3 py-2 bg-gray-200 rounded">Volver</button>
    <div v-if="loading">Cargando...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>
    <div v-else class="bg-white p-4 rounded shadow">
      <h2 class="text-xl font-bold">{{ plan.nombre }}</h2>
      <div class="text-sm text-gray-600 mb-2">Por: {{ plan.entrenador_nombre || '—' }}</div>
      <p class="mb-4">{{ plan.descripcion }}</p>
      <div class="border-t pt-4">
        <h3 class="font-semibold mb-2">Contenido del plan</h3>
        <div v-html="plan.contenido"></div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'

export default {
  name: 'ClientePlan',
  data() {
    return { plan: null, loading: true, error: null }
  },
  async mounted() {
    const id = this.$route.params.id
    try {
      const res = await api.get(`/api/planes`, { skipAuth: true })
      const list = await res.json()
      if (!res.ok) throw new Error(list.error || 'Error fetching plans')
      this.plan = list.find(p => p.id === Number(id)) || null
      if (!this.plan) this.error = 'Plan no encontrado'
    } catch (err) {
      this.error = err.message
    } finally {
      this.loading = false
    }
  }
}
</script>
