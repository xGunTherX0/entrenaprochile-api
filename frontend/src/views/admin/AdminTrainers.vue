<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">Perfiles de Entrenadores</h2>
    <div class="mb-4">
      <input v-model="q" @input="search" placeholder="Buscar por nombre" class="border px-2 py-1 w-full" />
    </div>

    <div v-if="loading">Cargando entrenadores...</div>
    <div v-if="!loading && trainers.length===0" class="text-sm text-gray-600">No hay entrenadores.</div>

    <div v-for="t in trainers" :key="t.entrenador_id" class="border p-3 rounded mb-2 bg-white">
      <div class="flex justify-between">
        <div>
          <div class="font-semibold">{{ t.nombre }} <small class="text-xs text-gray-500">(usuario: {{ t.usuario_id }})</small></div>
          <div class="text-xs text-gray-500">Speciality: {{ t.speciality || '—' }}</div>
        </div>
        <div>
          <button @click="openProfile(t.usuario_id)" class="px-2 py-1 bg-blue-600 text-white rounded text-sm">Ver perfil</button>
        </div>
      </div>
    </div>

    <div v-if="selectedUsuarioId" class="mt-6">
      <EntrenadorPublico :id="selectedUsuarioId" />
    </div>
  </div>
</template>

<script>
import api from '../../utils/api.js'
import EntrenadorPublico from '../../views/EntrenadorPublico.vue'
export default {
  name: 'AdminTrainers',
  components: { EntrenadorPublico },
  data() {
    return {
      trainers: [],
      loading: false,
      q: '',
      selectedUsuarioId: null
    }
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      this.loading = true
      try {
        const res = await api.get('/api/entrenadores')
        if (!res.ok) {
          this.trainers = []
          return
        }
        this.trainers = await res.json()
      } catch (e) {
        this.trainers = []
      } finally {
        this.loading = false
      }
    },
    search() {
      const q = (this.q || '').toLowerCase()
      if (!q) return this.load()
      this.trainers = this.trainers.filter(t => (t.nombre || '').toLowerCase().includes(q) || (t.speciality || '').toLowerCase().includes(q))
    },
    async openProfile(usuario_id) {
      // Use the public profile component to render the same view as clients.
      // Store only the usuario_id and let EntrenadorPublico fetch the public data.
      this.selectedUsuarioId = usuario_id
    }
  }
}
</script>
