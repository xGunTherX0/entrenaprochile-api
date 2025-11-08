<template>
  <div class="min-h-screen flex bg-gray-50">
    <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Cliente</h2>
      <ul>
        <li class="mb-2"><button @click="select('explorar')" :class="{'text-blue-600 font-semibold': activePanel==='explorar'}" class="text-left w-full">Explorar Rutinas</button></li>
        <li class="mb-2"><button @click="select('planes')" :class="{'text-blue-600 font-semibold': activePanel==='planes'}" class="text-left w-full">Mis Planes Nutricionales</button></li>
        <li class="mb-2"><button @click="select('mediciones')" :class="{'text-blue-600 font-semibold': activePanel==='mediciones'}" class="text-left w-full">Registro de Mediciones</button></li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>
    <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold">Cliente Dashboard</h1>

      <section v-if="activePanel === 'mediciones'">
        <p class="mt-4">Registro de Mediciones</p>

        <div class="mt-6 max-w-md bg-white p-4 rounded shadow">
        <form @submit.prevent="submitMedicion">
          <div class="mb-3">
            <label class="block text-sm">Peso (kg)</label>
            <input v-model.number="peso" type="number" step="0.1" class="w-full px-3 py-2 border rounded" />
          </div>
          <div class="mb-3">
            <label class="block text-sm">Altura (cm)</label>
            <input v-model.number="altura" type="number" step="0.1" class="w-full px-3 py-2 border rounded" />
          </div>
          <div class="mb-3">
            <label class="block text-sm">Circunferencia de Cintura (cm)</label>
            <input v-model.number="cintura" type="number" step="0.1" class="w-full px-3 py-2 border rounded" />
          </div>
          <div class="flex items-center justify-between">
            <button :disabled="saving" class="px-4 py-2 bg-green-600 text-white rounded">{{ saving ? 'Guardando...' : 'Guardar medición' }}</button>
            <div v-if="msg" class="text-sm text-green-600">{{ msg }}</div>
          </div>
        </form>
        </div>

      </section>

      <section v-if="activePanel === 'explorar'" class="mt-6">
        <h2 class="text-lg font-semibold mb-2">Explorar Rutinas</h2>
        <div v-if="loadingExplorar" class="bg-white p-4 rounded shadow">Cargando rutinas...</div>
        <div v-else>
          <div v-if="explorarRutinas.length === 0" class="bg-white p-4 rounded shadow">No hay rutinas públicas disponibles.</div>
          <div v-else class="bg-white p-4 rounded shadow">
            <!-- Buscar y filtros -->
            <div class="flex items-center justify-between mb-4">
              <div class="flex-1 pr-4">
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

            <!-- Grid de tarjetas -->
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
                  <button :disabled="savingFollowIds.includes(r.id)" @click="followRutina(r.id)" class="px-3 py-1 bg-green-600 text-white rounded">{{ savingFollowIds.includes(r.id) ? 'Guardando...' : 'Guardar rutina' }}</button>
                </div>
              </div>
            </div>

            <!-- Paginación simple -->
            <div class="mt-4 flex items-center justify-center space-x-2">
              <button :disabled="page<=1" @click="page--" class="px-3 py-1 border rounded">Anterior</button>
              <div>Página {{ page }} / {{ totalPages }}</div>
              <button :disabled="page>=totalPages" @click="page++" class="px-3 py-1 border rounded">Siguiente</button>
            </div>
          </div>
        </div>
      </section>

      <section v-if="activePanel === 'planes'" class="mt-6">
        <h2 class="text-lg font-semibold mb-2">Mis Planes Nutricionales</h2>
        <div class="bg-white p-4 rounded shadow">(Placeholder para planes)</div>
      </section>

      <section v-if="activePanel === 'mediciones'" class="mt-8">
        <h2 class="text-lg font-semibold mb-2">Historial de Mediciones</h2>
        <div v-if="loadingList">Cargando...</div>
        <table v-else class="min-w-full bg-white shadow rounded">
          <thead>
            <tr class="text-left">
              <th class="px-4 py-2">Fecha</th>
              <th class="px-4 py-2">Peso (kg)</th>
              <th class="px-4 py-2">Altura (cm)</th>
              <th class="px-4 py-2">Cintura (cm)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in mediciones" :key="m.id">
              <td class="px-4 py-2">{{ new Date(m.creado_en).toLocaleString() }}</td>
              <td class="px-4 py-2">{{ m.peso }}</td>
              <td class="px-4 py-2">{{ m.altura }}</td>
              <td class="px-4 py-2">{{ m.cintura }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <div class="mt-8 bg-white p-4 rounded shadow">
        <h2 class="text-lg font-semibold mb-2">Evolución de Peso</h2>
        <WeightChart :measurements="mediciones" />
      </div>

    </main>
  </div>
</template>

<script>
import WeightChart from '../components/WeightChart.vue'
import auth from '../utils/auth.js'
import api from '../utils/api.js'

export default {
  name: 'ClienteDashboard',
  components: { WeightChart },
  data() {
    return {
      peso: null,
      altura: null,
      cintura: null,
      saving: false,
      msg: '',
      mediciones: [],
      loadingList: false
      ,
      explorarRutinas: [],
      loadingExplorar: false,
      selectedTrainerId: null
      ,
      activePanel: 'mediciones',
      // UI: search + pagination
      searchQuery: '',
      page: 1,
      pageSize: 6,
      savingFollowIds: []
    }
  },
  methods: {
    async submitMedicion() {
      this.saving = true
      this.msg = ''
      try {
        const user_id = auth.getSession().user_id
        const res = await api.post('/api/mediciones', { peso: this.peso, altura: this.altura, cintura: this.cintura })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Error al guardar')
        this.msg = 'Medición guardada con id ' + data.id
        this.peso = this.altura = this.cintura = null
        // refrescar la lista
        this.fetchMediciones()
      } catch (err) {
        this.msg = err.message
      } finally {
        this.saving = false
      }
    },

    async fetchMediciones() {
      this.loadingList = true
      this.mediciones = []
      try {
    const user_id = auth.getSession().user_id
    const res = await api.get(`/api/mediciones/${user_id}`)
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Error al obtener mediciones')
    this.mediciones = data
      } catch (err) {
        console.error(err)
      } finally {
        this.loadingList = false
      }
    },

    async fetchRutinasPublicas() {
      this.loadingExplorar = true
      this.explorarRutinas = []
      try {
        const res = await api.get('/api/rutinas/public', { skipAuth: true })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Error al obtener rutinas')
        this.explorarRutinas = data
      } catch (err) {
        console.error('fetchRutinasPublicas', err)
      } finally {
        this.loadingExplorar = false
      }
    },

    selectTrainer(trainerId) {
      this.selectedTrainerId = trainerId
      this.page = 1
    },

    onSearch() {
      this.page = 1
    },

    async followRutina(rutinaId) {
      if (!rutinaId) return
      // optimistically show saving state per-rutina
      if (!this.savingFollowIds.includes(rutinaId)) this.savingFollowIds.push(rutinaId)
      try {
        const res = await api.post(`/api/rutinas/${rutinaId}/seguir`, {})
        const body = await res.json()
        if (!res.ok) throw new Error(body.error || 'Error guardando rutina')
        // success: you may show a toast or update UI
        // remove saving flag
      } catch (err) {
        console.error('followRutina', err)
        // errors will be handled by global api wrapper (401->redirect) or logged here
      } finally {
        const idx = this.savingFollowIds.indexOf(rutinaId)
        if (idx !== -1) this.savingFollowIds.splice(idx, 1)
      }
    },

    openRutinaDetail(rutinaId) {
      this.$router.push(`/cliente/rutina/${rutinaId}`)
    },

    // Navegar entre paneles y sincronizar con la ruta
    select(panel) {
      if (!panel) return
      this.activePanel = panel
      // actualizar la URL para que sea shareable
      try {
        this.$router.push(`/cliente/${panel}`)
      } catch (e) {
        // ignore navigation errors
      }
      if (panel === 'mediciones') this.fetchMediciones()
      if (panel === 'explorar') this.fetchRutinasPublicas()
    },

    logout() {
      auth.clearSession()
      this.$router.push('/')
    }
  },
  computed: {
    trainers() {
      // build list of unique trainers from explorarRutinas
      const map = {}
      this.explorarRutinas.forEach(r => {
        const id = r.entrenador_id || ('_' + (r.entrenador_nombre || ''))
        if (!map[id]) map[id] = { entrenador_id: r.entrenador_id, entrenador_nombre: r.entrenador_nombre }
      })
      return Object.values(map)
    },
    filteredRutinas() {
      // apply trainer filter and searchQuery
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
  mounted() {
    const parts = (this.$route && this.$route.path) ? this.$route.path.split('/') : []
    const panel = parts[2] || 'mediciones'
    if (panel) this.activePanel = panel
    if (this.activePanel === 'mediciones') this.fetchMediciones()
    if (this.activePanel === 'explorar') this.fetchRutinasPublicas()
    this.$watch(() => this.$route.path, (newPath) => {
      const p = (newPath || '').split('/')[2] || 'mediciones'
      if (p) this.select(p)
    })
  }
}
</script>

<style scoped>
.trainer-list button {
  text-align: left;
  width: 100%;
}
</style>
