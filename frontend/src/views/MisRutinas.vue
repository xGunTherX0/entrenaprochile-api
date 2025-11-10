<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Mis Rutinas Guardadas</h1>
    <div class="bg-white p-4 rounded shadow">
        <div class="flex items-center justify-between mb-4">
          <div v-if="loading">Cargando tus rutinas guardadas...</div>
          <div class="w-1/3">
            <input v-model="searchQuery" placeholder="Buscar rutinas..." class="w-full px-3 py-2 border rounded" />
          </div>
        </div>
        <div v-if="!loading">
          <div v-if="filteredRutinas.length===0" class="text-sm text-gray-600">No tienes rutinas guardadas.</div>
          <ul class="mt-2 space-y-2">
            <li v-for="r in filteredRutinas" :key="r.id" class="p-3 border rounded bg-white flex justify-between items-center">
              <div>
                <div class="font-semibold">{{ r.nombre }} <span v-if="(r._localOnly) || (localSavedRutinas && localSavedRutinas.includes(Number(r.id)))" class="ml-2 text-xs px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded">Guardada localmente</span></div>
                <div class="text-sm text-gray-600">{{ r.descripcion }}</div>
              </div>
              <div class="space-x-2">
                <button @click="openRutinaDetail(r.id)" class="px-3 py-1 bg-blue-600 text-white rounded">Ver</button>
                <button @click="unfollowRutina(r.id)" class="px-3 py-1 bg-red-600 text-white rounded">Eliminar</button>
              </div>
            </li>
          </ul>
        </div>
      </div>
  </div>
</template>

<script>
import api from '../utils/api.js'
import auth from '../utils/auth.js'

export default {
  name: 'MisRutinas',
  data() {
    return {
      misRutinas: [],
      loading: false,
      searchQuery: '',
      localSavedRutinas: []
    }
  },
  methods: {
    async fetchMisRutinas() {
      this.loading = true
      this.misRutinas = []
      try {
        const res = await api.get('/api/rutinas/mis')
        if (res && res.ok) {
          this.misRutinas = await res.json()
        }
        // Merge any locally-saved rutina ids (fallback when server save failed)
        try {
          const saved = JSON.parse(localStorage.getItem('saved_rutinas') || '[]')
          this.localSavedRutinas = Array.isArray(saved) ? saved : []
        } catch (e) {
          this.localSavedRutinas = []
        }
        // For any local saved id not present in server result, add a placeholder entry
        const existingIds = new Set((this.misRutinas || []).map(r => Number(r.id)))
        for (const id of this.localSavedRutinas) {
          if (!existingIds.has(Number(id))) {
            this.misRutinas.push({ id: Number(id), nombre: 'Guardado localmente', descripcion: '', nivel: '', es_publica: false, _localOnly: true })
          }
        }
      } catch (e) {
        console.error('fetchMisRutinas', e)
      } finally {
        this.loading = false
      }
    },
    openRutinaDetail(id) {
      if (!id) return
      this.$router.push(`/cliente/rutina/${id}`)
    },
    async unfollowRutina(rutinaId) {
      if (!rutinaId) return
      if (!confirm('¿Eliminar esta rutina guardada?')) return
      try {
        const res = await api.del(`/api/rutinas/${rutinaId}/seguir`)
        if (res && res.ok) {
          this.misRutinas = this.misRutinas.filter(r => r.id !== rutinaId)
        } else {
          let body = {}
          try { body = await res.json() } catch (e) {}
          throw new Error(body.error || 'Error eliminando rutina guardada')
        }
      } catch (err) {
        console.error('unfollowRutina failed', err)
        try { alert('No se pudo eliminar la rutina guardada: ' + (err.message || err)) } catch (e) {}
      }
    }
  },
  computed: {
    filteredRutinas() {
      const q = (this.searchQuery || '').trim().toLowerCase()
      if (!q) return this.misRutinas || []
      return (this.misRutinas || []).filter(r => {
        return (r.nombre || '').toLowerCase().includes(q) || (r.descripcion || '').toLowerCase().includes(q) || (r.nivel || '').toLowerCase().includes(q)
      })
    }
  },
  mounted() {
    this.fetchMisRutinas()
  }
}
</script>
