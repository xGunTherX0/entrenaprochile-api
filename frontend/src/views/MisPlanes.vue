<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Mis Planes Nutricionales</h1>
    <div class="bg-white p-4 rounded shadow">
      <div class="flex items-center justify-between mb-4">
        <div v-if="loading">Cargando tus solicitudes...</div>
        <div class="w-1/3">
          <input v-model="searchQuery" placeholder="Buscar en mis solicitudes..." class="w-full px-3 py-2 border rounded" />
        </div>
      </div>

      <div v-if="!loading">
        <h3 class="font-semibold mb-2">Mis Solicitudes de Plan</h3>
        <div v-if="misSolicitudes.length===0" class="text-sm text-gray-600">No has solicitado ningún plan aún.</div>
        <ul class="mt-2 space-y-2">
          <li v-for="s in filteredSolicitudes" :key="s.id" class="p-3 border rounded bg-white">
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <div class="font-semibold">{{ s.rutina_nombre || ('Plan ' + (s.plan_id || s.id)) }}</div>
                <div class="text-sm text-gray-600">Estado: <span :class="statusClass(s.estado)">{{ s.estado }}</span> — {{ s.creado_en ? new Date(s.creado_en).toLocaleString() : '' }}</div>
                <div v-if="s.nota" class="text-sm mt-1">Nota: {{ s.nota }}</div>
              </div>
              <div class="ml-4 flex-shrink-0 space-y-2">
                <div class="space-x-2">
                  <button
                    :disabled="!canViewPlan(s)"
                    @click="openPlanFromSolicitud(s)"
                    :title="canViewPlan(s) ? 'Ver plan' : 'El entrenador no ha autorizado ver este plan'"
                    class="px-3 py-1 rounded"
                    :class="canViewPlan(s) ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600 cursor-not-allowed'"
                  >
                    Ver plan
                  </button>
                  <button v-if="s.estado !== 'cancelado'" @click="cancelarSolicitud(s.id)" :disabled="cancellingIds.includes(s.id)" class="px-3 py-1 bg-red-600 text-white rounded">{{ cancellingIds.includes(s.id) ? 'Cancelando...' : 'Cancelar' }}</button>
                </div>
                <div v-if="s.estado === 'cancelado'" class="text-sm text-red-600">Solicitud cancelada</div>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'

export default {
  name: 'MisPlanes',
  data() {
    return {
      misSolicitudes: [],
      loading: false,
      searchQuery: '',
      cancellingIds: []
    }
  },
  methods: {
    isPlanSolicitud(s) {
      if (!s) return false
      const planId = Number(s.plan_id)
      const rutinaId = Number(s.rutina_id)
      // plan if plan_id is a positive number and rutina_id is not a positive number
      return !isNaN(planId) && planId > 0 && (isNaN(rutinaId) || rutinaId <= 0)
    },
    async fetchSolicitudes() {
      this.loading = true
      try {
        const r2 = await api.get('/api/solicitudes/mis')
          if (r2 && r2.ok) {
          const all = await r2.json()
          // By default hide already-cancelled solicitudes and show only plan-type solicitudes
          // Defensive: treat as plan-type only when plan_id is explicitly present (not null/undefined)
          this.misSolicitudes = Array.isArray(all) ? all.filter(s => s && (s.estado || '').toString().toLowerCase() !== 'cancelado') : []
          // Use robust numeric checks to avoid string "null" or "0" being misclassified
          this.misSolicitudes = this.misSolicitudes.filter(s => this.isPlanSolicitud(s))
        }
      } catch (e) {
        console.error('fetch mis solicitudes failed', e)
      }
      this.loading = false
    },
    openPlanDetail(id) {
      if (!id) return
      this.$router.push(`/cliente/plan/${id}`)
    },
    canViewPlan(s) {
      try {
        if (!s) return false
        const estado = (s.estado || '').toString().toLowerCase()
        return estado === 'aceptado' || estado === 'aceptada' || estado === 'accepted'
      } catch (e) {
        return false
      }
    },
    async cancelarSolicitud(solicitudId) {
      if (!solicitudId) return
      if (!this.cancellingIds.includes(solicitudId)) this.cancellingIds.push(solicitudId)
      try {
  const res = await api.del(`/api/solicitudes/${solicitudId}`)
        if (res && res.ok) {
          // remove the cancelled solicitud from local list so it disappears immediately
          this.misSolicitudes = (this.misSolicitudes || []).filter(item => item.id !== solicitudId)
        } else {
          const b = await res.json().catch(()=>({}));
          throw new Error(b.error || 'Error cancelando solicitud')
        }
      } catch (e) {
        console.error('cancelarSolicitud failed', e)
        try { alert('No se pudo cancelar la solicitud: ' + (e.message || e)) } catch (ee) {}
      } finally {
        const i = this.cancellingIds.indexOf(solicitudId)
        if (i !== -1) this.cancellingIds.splice(i, 1)
      }
    },
    statusClass(estado) {
      if (!estado) return ''
      const e = estado.toString().toLowerCase()
      if (e === 'aceptado' || e === 'aceptada') return 'text-green-600'
      if (e === 'pendiente') return 'text-yellow-600'
      if (e === 'cancelado') return 'text-red-600'
      return ''
    },
    openPlanFromSolicitud(solicitud) {
      if (!solicitud) return
      if (!this.canViewPlan(solicitud)) {
        try { alert('El entrenador no ha autorizado ver este plan todavía.') } catch (e) {}
        return
      }
      const planId = solicitud.plan_id
      if (planId) {
        this.$router.push({ path: `/cliente/plan/${planId}`, query: { solicitudId: solicitud.id } })
        return
      }
      if (solicitud.rutina_id) {
        try { alert('Aún no hay un plan asignado a esta solicitud. Intenta más tarde o contacta con tu entrenador.') } catch (e) {}
        return
      }
      try { alert('Solicitud inválida: sin rutina ni plan asociado.') } catch (e) {}
    }
  },
  mounted() {
    this.fetchSolicitudes()
  }
  ,
  computed: {
    filteredSolicitudes() {
      const q = (this.searchQuery || '').trim().toLowerCase()
      if (!q) return this.misSolicitudes || []
      return (this.misSolicitudes || []).filter(s => {
        const nombre = (s.rutina_nombre || '').toString().toLowerCase()
        const nota = (s.nota || '').toString().toLowerCase()
        return nombre.includes(q) || nota.includes(q) || (s.estado || '').toLowerCase().includes(q)
      })
    }
  }
}
</script>

<style scoped>
.text-red-600 { color: #e3342f; }
</style>
