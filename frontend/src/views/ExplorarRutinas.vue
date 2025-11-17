<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Explorar Rutinas</h1>

    <div class="bg-white p-4 rounded shadow">
      <div class="flex items-center justify-between mb-4">
        <div class="w-1/3">
          <input v-model="searchQuery" @input="onSearch" placeholder="Buscar por nombre o nivel..." class="w-full px-3 py-2 border rounded" />
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

      <div v-if="loading" class="bg-white p-4 rounded shadow">Cargando rutinas...</div>
      <div v-else>
        <div v-if="explorarRutinas.length === 0" class="bg-white p-4 rounded shadow">No hay rutinas públicas disponibles.</div>
        <div v-else class="bg-white p-4 rounded shadow">
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="r in paginatedRutinas" :key="r.id" class="bg-white border rounded p-4 shadow hover:shadow-md">
              <div class="flex justify-between items-start">
                <div>
                  <h3 class="font-semibold text-lg cursor-pointer" @click="openRutinaDetail(r.id)">{{ r.nombre }}</h3>
                  <div class="text-sm text-gray-600">{{ r.nivel }} • {{ r.entrenador_nombre || '—' }}</div>
                </div>
                <div class="text-xs text-gray-500">{{ r.creado_en ? new Date(r.creado_en).toLocaleDateString() : '' }}</div>
              </div>
              <p class="mt-3 text-sm text-gray-700">{{ r.descripcion }}</p>
                <div class="mt-4 flex items-center justify-between">
                <div class="space-x-2">
                  <button @click="openRutinaDetail(r.id)" class="px-3 py-1 bg-blue-600 text-white rounded">Ver</button>
                </div>
                <button :disabled="savingFollowIds.includes(r.id) || requestedRutinaIds.includes(r.id)" @click="solicitarRutina(r.id)" class="px-3 py-1 bg-green-600 text-white rounded">{{ savingFollowIds.includes(r.id) ? 'Enviando...' : (requestedRutinaIds.includes(r.id) ? 'Solicitud pendiente' : 'Solicitar rutina') }}</button>
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
  name: 'ExplorarRutinas',
  data() {
    return {
      explorarRutinas: [],
      loading: false,
      searchQuery: '',
      selectedTrainerId: null,
      page: 1,
      pageSize: 6,
      savingFollowIds: [],
      requestedRutinaIds: [],
      localSavedRutinas: []
    }
  },
  computed: {
    trainers() {
      // Defensive: ensure explorarRutinas is an array before iterating
      const arr = Array.isArray(this.explorarRutinas) ? this.explorarRutinas : []
      const byId = {}
      for (let i = 0; i < arr.length; i++) {
        const r = arr[i]
        const id = r && (r.entrenador_id != null ? r.entrenador_id : ('_' + (r.entrenador_nombre || '')))
        if (!byId[id]) {
          byId[id] = { entrenador_id: r ? r.entrenador_id : null, entrenador_nombre: r ? r.entrenador_nombre : null, entrenador_id_usuario: r ? r.entrenador_usuario_id : null }
        }
      }
      // Return as an array without assuming Object.values exists in older runtimes
      return Object.keys(byId).map(k => byId[k])
    },
    filteredRutinas() {
      let list = Array.isArray(this.explorarRutinas) ? this.explorarRutinas.slice() : []
      if (this.selectedTrainerId) {
        list = list.filter(r => r && r.entrenador_id === this.selectedTrainerId)
      }
      if (this.searchQuery && this.searchQuery.trim().length > 0) {
        const q = this.searchQuery.trim().toLowerCase()
        list = list.filter(r => (r && ((r.nombre || '').toLowerCase().includes(q) || (r.nivel || '').toLowerCase().includes(q) || (r.descripcion || '').toLowerCase().includes(q))))
      }
      return list
    },
    totalPages() {
      const total = Math.max(1, Math.ceil((this.filteredRutinas || []).length / this.pageSize))
      return total
    },
    paginatedRutinas() {
      const start = (this.page - 1) * this.pageSize
      return (this.filteredRutinas || []).slice(start, start + this.pageSize)
    }
  },
  methods: {
    onSearch() { this.page = 1 },
    selectTrainer(id) { this.selectedTrainerId = id; this.page = 1 },
    async fetchRutinasPublicas() {
      this.loading = true
      this.explorarRutinas = []
      try {
        const res = await api.get('/api/rutinas/public', { skipAuth: true })
        const data = await res.json()
        if (res && res.ok) this.explorarRutinas = data
        try {
          const saved = JSON.parse(localStorage.getItem('saved_rutinas') || '[]')
          this.localSavedRutinas = Array.isArray(saved) ? saved : []
        } catch (e) { this.localSavedRutinas = [] }
      } catch (err) {
        console.error('fetchRutinasPublicas', err)
      } finally { this.loading = false }
    },
    async fetchMisSolicitudes() {
      try {
        const r = await api.get('/api/solicitudes/mis')
        if (r && r.ok) {
          const all = await r.json()
          // Only consider solicitudes that are active (pendiente) or already aceptadas.
          this.requestedRutinaIds = Array.isArray(all) ? all.filter(s => s && (() => { const rid = Number(s.rutina_id); return !isNaN(rid) && rid > 0 && (s.estado === 'pendiente' || s.estado === 'aceptado') })()).map(s => Number(s.rutina_id)) : []
        }
      } catch (e) {
        // ignore unauthenticated or other errors
      }
    },
    openRutinaDetail(id) { if (!id) return; this.$router.push(`/cliente/rutina/${id}`) },
    async followRutina(rutinaId) {
      // kept for backwards compatibility but now delegates to solicitarRutina
      return this.solicitarRutina(rutinaId)
    }
    ,
    async solicitarRutina(rutinaId) {
      if (!rutinaId) return
      try {
        const res = await api.post(`/api/rutinas/${rutinaId}/solicitar`, {})
        const body = await res.json()
        if (!res.ok) throw new Error(body.error || 'Error solicitando rutina')
        // Update UI immediately: if the server returned a pending or accepted solicitud,
        // mark this rutina as requested so the button disables without needing a refresh.
        try {
          const estado = body.estado || 'pendiente'
          if ((estado === 'pendiente' || estado === 'aceptado') && !this.requestedRutinaIds.includes(rutinaId)) {
            this.requestedRutinaIds.push(rutinaId)
          }
        } catch (e) {
          // ignore UI update failures
        }
        // navigate to Mis Rutinas where solicitudes are shown
        try { this.$router.push('/cliente/misrutinas') } catch (e) {}
        // notify user
        try { (await import('../utils/toast.js')).default.show('Solicitud creada. Revisa Mis Rutinas para ver el estado.', 3000) } catch (e) { alert('Solicitud creada') }
      } catch (err) {
        console.error('solicitarRutina failed', err)
        try { alert('No se pudo solicitar el plan: ' + (err.message || err)) } catch (e) {}
      }
    }
  },
  async mounted() { if (!this.explorarRutinas.length) await this.fetchRutinasPublicas(); await this.fetchMisSolicitudes() }
}
</script>
