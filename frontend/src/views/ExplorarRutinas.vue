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
            <button v-for="t in trainers" :key="t.entrenador_id" @click="selectTrainer(t.entrenador_id)" :class="{'font-semibold text-blue-600': selectedTrainerId===t.entrenador_id}" class="px-2 py-1 rounded bg-gray-50 w-full text-left">{{ t.entrenador_nombre || '—' }}</button>
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
                <button @click="openRutinaDetail(r.id)" class="px-3 py-1 bg-blue-600 text-white rounded">Ver</button>
                <button :disabled="savingFollowIds.includes(r.id) || localSavedRutinas.includes(r.id)" @click="followRutina(r.id)" class="px-3 py-1 bg-green-600 text-white rounded">{{ savingFollowIds.includes(r.id) ? 'Guardando...' : (localSavedRutinas.includes(r.id) ? 'Guardado' : 'Guardar rutina') }}</button>
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
      localSavedRutinas: []
    }
  },
  computed: {
    trainers() {
      const map = {}
      (this.explorarRutinas || []).forEach(r => {
        const id = r.entrenador_id || ('_' + (r.entrenador_nombre || ''))
        if (!map[id]) map[id] = { entrenador_id: r.entrenador_id, entrenador_nombre: r.entrenador_nombre }
      })
      // Avoid relying on Object.values (compatibility); use keys->map
      return Object.keys(map).map(k => map[k])
    },
    filteredRutinas() {
      let list = this.explorarRutinas || []
      if (this.selectedTrainerId) {
        list = list.filter(r => r.entrenador_id === this.selectedTrainerId)
      }
      if (this.searchQuery && this.searchQuery.trim().length > 0) {
        const q = this.searchQuery.trim().toLowerCase()
        list = list.filter(r => (r.nombre || '').toLowerCase().includes(q) || (r.nivel || '').toLowerCase().includes(q) || (r.descripcion || '').toLowerCase().includes(q))
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
    openRutinaDetail(id) { if (!id) return; this.$router.push(`/cliente/rutina/${id}`) },
    async followRutina(rutinaId) {
      if (!rutinaId) return
      if (!this.savingFollowIds.includes(rutinaId)) this.savingFollowIds.push(rutinaId)
      try {
        const res = await api.post(`/api/rutinas/${rutinaId}/seguir`, {})
        const body = await res.json()
        if (!res.ok) throw new Error(body.error || 'Error guardando rutina')
        if (!this.localSavedRutinas.includes(rutinaId)) {
          this.localSavedRutinas.push(rutinaId)
          localStorage.setItem('saved_rutinas', JSON.stringify(this.localSavedRutinas))
        }
      } catch (err) {
        console.error('followRutina, falling back to local save', err)
        try {
          if (!this.localSavedRutinas.includes(rutinaId)) {
            this.localSavedRutinas.push(rutinaId)
            localStorage.setItem('saved_rutinas', JSON.stringify(this.localSavedRutinas))
          }
        } catch (e) { console.error('local save failed', e) }
      } finally {
        const idx = this.savingFollowIds.indexOf(rutinaId)
        if (idx !== -1) this.savingFollowIds.splice(idx, 1)
      }
    }
  },
  mounted() { if (!this.explorarRutinas.length) this.fetchRutinasPublicas() }
}
</script>
