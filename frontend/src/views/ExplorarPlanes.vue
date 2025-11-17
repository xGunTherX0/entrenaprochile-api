<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Explorar Planes Nutricionales</h1>
    <div class="bg-white p-4 rounded shadow">
      <div class="flex items-start justify-between mb-4">
        <div class="w-1/3">
          <input v-model="searchQuery" @input="onSearch" placeholder="Buscar por nombre o descripción..." class="w-full px-3 py-2 border rounded" />
        </div>
        <aside class="w-60 trainer-list">
          <h3 class="font-semibold mb-2">Entrenadores</h3>
          <div class="space-y-2">
            <button :class="{'font-semibold text-blue-600': selectedTrainerId===null}" @click="selectTrainer(null)" class="px-2 py-1 rounded bg-gray-50 w-full text-left">Todos</button>
            <div v-for="t in trainers" :key="t.entrenador_id" class="flex items-center justify-between">
              <button @click="selectTrainer(t.entrenador_id)" :class="{'font-semibold text-blue-600': selectedTrainerId===t.entrenador_id}" class="px-2 py-1 rounded bg-gray-50 w-full text-left">{{ t.entrenador_nombre || '—' }}</button>
              <router-link :to="{ name: 'EntrenadorPublico', params: { id: t.entrenador_id_usuario || t.entrenador_id } }" class="ml-2 text-sm text-blue-600">Ver perfil</router-link>
            </div>
          </div>
        </aside>
      </div>

      <div v-if="loading" class="bg-white p-4 rounded shadow">Cargando planes...</div>
      <div v-else>
        <div v-if="filteredPlanes.length===0" class="text-sm text-gray-600">No hay planes públicos disponibles.</div>
        <div v-else>
          <div class="grid grid-cols-1 gap-4">
            <div v-for="p in paginatedPlanes" :key="p.id" class="p-3 border rounded bg-gray-50 flex justify-between items-center">
              <div>
                <div class="font-semibold">{{ p.nombre }}</div>
                <div class="text-sm text-gray-600">{{ p.descripcion }}</div>
                <div class="text-xs text-gray-500">Por: {{ p.entrenador_nombre || '—' }}</div>
              </div>
              <div class="space-x-2">
                <button @click="openPlanDetail(p.id)" class="px-3 py-1 bg-blue-600 text-white rounded">Ver</button>
                <button @click="elegirPlan(p.id)" :disabled="loadingIds.includes(p.id) || requestedPlanIds.includes(p.id)" class="px-3 py-1 bg-green-600 text-white rounded">{{ loadingIds.includes(p.id) ? 'Elegiendo...' : (requestedPlanIds.includes(p.id) ? 'Solicitud pendiente' : 'Elegir plan') }}</button>
              </div>
            </div>
          </div>

          <div class="mt-4 flex items-center justify-center space-x-2">
            <button :disabled="page<=1" @click="page--" class="px-3 py-1 border rounded">Anterior</button>
            <div>Página {{ page }} / {{ totalPages }}</div>
            <button :disabled="page>=totalPages" @click="page++" class="px-3 py-1 border rounded">Siguiente</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'

export default {
  name: 'ExplorarPlanes',
  data() {
    return {
      planes: [],
      loading: false,
      loadingIds: [],
      requestedPlanIds: [],
      searchQuery: '',
      selectedTrainerId: null,
      page: 1,
      pageSize: 6
    }
  },
  computed: {
    trainers() {
      const arr = Array.isArray(this.planes) ? this.planes : []
      const byId = {}
      for (let i = 0; i < arr.length; i++) {
        const p = arr[i]
        const id = p && (p.entrenador_id != null ? p.entrenador_id : ('_' + (p.entrenador_nombre || '')))
        if (!byId[id]) {
          byId[id] = { entrenador_id: p ? p.entrenador_id : null, entrenador_nombre: p ? p.entrenador_nombre : null, entrenador_id_usuario: p ? p.entrenador_usuario_id : null }
        }
      }
      return Object.keys(byId).map(k => byId[k])
    },
    filteredPlanes() {
      let list = Array.isArray(this.planes) ? this.planes.slice() : []
      if (this.selectedTrainerId) {
        list = list.filter(p => p && p.entrenador_id === this.selectedTrainerId)
      }
      if (this.searchQuery && this.searchQuery.trim().length > 0) {
        const q = this.searchQuery.trim().toLowerCase()
        list = list.filter(p => (p && ((p.nombre || '').toLowerCase().includes(q) || (p.descripcion || '').toLowerCase().includes(q))))
      }
      return list
    },
    totalPages() {
      const total = Math.max(1, Math.ceil((this.filteredPlanes || []).length / this.pageSize))
      return total
    },
    paginatedPlanes() {
      const start = (this.page - 1) * this.pageSize
      return (this.filteredPlanes || []).slice(start, start + this.pageSize)
    }
  },
  methods: {
    onSearch() { this.page = 1 },
    selectTrainer(id) { this.selectedTrainerId = id; this.page = 1 },
    async fetchPlanes() {
      this.loading = true
      try {
        const res = await api.get('/api/planes', { skipAuth: true })
        if (res && res.ok) this.planes = await res.json()
      } catch (e) {
        console.error('fetchPlanes failed', e)
      } finally {
        this.loading = false
      }
    },
    async fetchMisSolicitudes() {
      try {
        const r = await api.get('/api/solicitudes/mis')
        if (r && r.ok) {
          const all = await r.json()
          // Only include active solicitudes (pendiente) or accepted; allow re-request after rechazo/cancelado
          this.requestedPlanIds = Array.isArray(all) ? all.filter(s => s && (() => { const pid = Number(s.plan_id); return !isNaN(pid) && pid > 0 && (s.estado === 'pendiente' || s.estado === 'aceptado') })()).map(s => Number(s.plan_id)) : []
        }
      } catch (e) {
        // ignore unauthenticated
      }
    },
    openPlanDetail(id) {
      if (!id) return
      this.$router.push(`/cliente/plan/${id}`)
    },
    async elegirPlan(planId) {
      if (!planId) return
      if (!this.loadingIds.includes(planId)) this.loadingIds.push(planId)
      try {
        const res = await api.post(`/api/planes/${planId}/solicitar`)
        const body = await (res && res.json ? res.json().catch(() => ({})) : Promise.resolve({}))
        if (res && res.ok) {
          try {
            const estado = body.estado || 'pendiente'
            if ((estado === 'pendiente' || estado === 'aceptado') && !this.requestedPlanIds.includes(planId)) {
              this.requestedPlanIds.push(planId)
            }
          } catch (e) {}
          // go to Mis Planes screen where solicitudes are listed
          this.$router.push('/cliente/planes')
        } else {
          throw new Error(body.error || 'Error al elegir plan')
        }
      } catch (e) {
        console.error('elegirPlan failed', e)
        try { alert('No se pudo elegir el plan: ' + (e.message || e)) } catch (ee) {}
      } finally {
        const i = this.loadingIds.indexOf(planId)
        if (i !== -1) this.loadingIds.splice(i, 1)
      }
    }
  },
  mounted() {
    this.fetchPlanes()
    this.fetchMisSolicitudes()
  }
}
</script>

<style scoped>
</style>
