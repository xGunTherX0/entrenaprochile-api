<template>
  <div>
    <h2 class="text-lg font-semibold">Métricas</h2>
    <div v-if="metrics" class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
      <div class="p-4 bg-white rounded shadow">
        <div class="text-sm text-gray-500">Usuarios (totales)</div>
        <div class="text-2xl font-bold">{{ metrics.total_users ?? 0 }}</div>
      </div>
      <div class="p-4 bg-white rounded shadow">
        <div class="text-sm text-gray-500">Clientes (solo)</div>
        <div class="text-2xl font-bold">{{ metrics.clientes_only ?? metrics.total_clientes ?? 0 }}</div>
      </div>
      <div class="p-4 bg-white rounded shadow">
        <div class="text-sm text-gray-500">Entrenadores</div>
        <div class="text-2xl font-bold">{{ metrics.total_entrenadores ?? metrics.entrenadores_only ?? 0 }}</div>
      </div>
    </div>
    <div v-else class="mt-3 text-sm text-gray-500">
      <div v-if="loadingMetrics">Cargando métricas...</div>
      <div v-else-if="metricsError" class="text-red-600">{{ metricsError }}</div>
      <div v-else class="text-gray-500">Cargando métricas...</div>
    </div>
  </div>
</template>

<script>
import auth from '../../utils/auth.js'
import api from '../../utils/api.js'
export default {
  name: 'AdminMetricas',
  data() {
    return { metrics: null, metricsError: null, loadingMetrics: false }
  },
  methods: {
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
    }
  },
  mounted() {
    this.loadMetrics()
  }
}
</script>
