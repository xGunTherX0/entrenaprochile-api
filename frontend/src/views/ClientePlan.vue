<template>
  <div class="p-6">
    <button @click="$router.back()" class="mb-4 px-3 py-2 bg-gray-200 rounded">Volver</button>
    <div v-if="loading">Cargando...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>
    <div v-else class="bg-white p-4 rounded shadow">
      <div v-if="planForbidden" class="text-yellow-700 mb-4">
        Este plan no está público. No puedes ver su contenido completo.
      </div>
      <h2 class="text-xl font-bold">{{ plan ? plan.nombre : 'Plan privado' }}</h2>
      <div class="text-sm text-gray-600 mb-2">Por: {{ plan ? plan.entrenador_nombre : '—' }}</div>
      <p class="mb-4">{{ plan ? plan.descripcion : '' }}</p>
      <div class="border-t pt-4">
        <h3 class="font-semibold mb-2">Contenido del plan</h3>
        <div v-if="plan && !planForbidden" v-html="plan.contenido"></div>
        <div v-else class="text-sm text-gray-600">Contenido oculto</div>
      </div>
      <!-- 'Volver a solicitudes' button removed; top 'Volver' button remains -->
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'

export default {
  name: 'ClientePlan',
  data() {
    return { plan: null, loading: true, error: null, solicitudId: null, planForbidden: false }
  },
  methods: {
    async fetchPlanById(id) {
      this.loading = true
      this.error = null
      this.planForbidden = false
      try {
        const res = await api.get(`/api/planes/${id}`)
        const body = await res.json()
        if (!res.ok) {
          if (res.status === 403) {
            // Plan is not public — show friendly message but don't force a redirect
            this.planForbidden = true
            this.error = body.error || 'No autorizado para ver este plan.'
          } else {
            throw new Error(body.error || 'Error fetching plan')
          }
        } else {
          this.plan = body
        }
      } catch (err) {
        this.error = err.message || String(err)
      } finally {
        this.loading = false
      }
    },
    async cancelSolicitud() {
      if (!this.solicitudId) return
      if (!confirm('¿Seguro que quieres cancelar esta solicitud?')) return
      try {
        const res = await api.del(`/api/solicitudes/${this.solicitudId}`)
        const body = await res.json()
        if (!res.ok) throw new Error(body.error || 'Error cancelando solicitud')
        try { alert('Solicitud cancelada') } catch (e) {}
        this.$router.push('/cliente/planes')
      } catch (err) {
        try { alert('No se pudo cancelar: ' + (err.message || err)) } catch (e) {}
      }
    }
  },
  async mounted() {
    const id = this.$route.params.id
    // solicitud id may be passed via query string
    this.solicitudId = this.$route.query && this.$route.query.solicitudId ? this.$route.query.solicitudId : null
    if (id) await this.fetchPlanById(id)
  }
}
</script>
