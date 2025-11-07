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
        <div class="bg-white p-4 rounded shadow">(Placeholder para explorar rutinas)</div>
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
      activePanel: 'mediciones'
    }
  },
  methods: {
    async submitMedicion() {
      this.saving = true
      this.msg = ''
      try {
  // Usar VITE_API_BASE en build; fallback a la URL pública del backend si no está definida
  const base = import.meta.env.VITE_API_BASE || 'https://entrenaprochile-api.onrender.com'
        const user_id = auth.getSession().user_id
        const headers = { 'Content-Type': 'application/json', ...auth.authHeaders() }
        const res = await fetch(`${base}/api/mediciones`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ peso: this.peso, altura: this.altura, cintura: this.cintura })
        })
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
  // Usar VITE_API_BASE en build; fallback a la URL pública del backend si no está definida
  const base = import.meta.env.VITE_API_BASE || 'https://entrenaprochile-api.onrender.com'
        const user_id = auth.getSession().user_id
  const headers = { ...auth.authHeaders() }
  const res = await fetch(`${base}/api/mediciones/${user_id}`, { headers })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Error al obtener mediciones')
        this.mediciones = data
      } catch (err) {
        console.error(err)
      } finally {
        this.loadingList = false
      }
    },

    logout() {
      auth.clearSession()
      this.$router.push('/')
    }
  },
  mounted() {
    const parts = (this.$route && this.$route.path) ? this.$route.path.split('/') : []
    const panel = parts[2] || 'mediciones'
    if (panel) this.activePanel = panel
    if (this.activePanel === 'mediciones') this.fetchMediciones()
    this.$watch(() => this.$route.path, (newPath) => {
      const p = (newPath || '').split('/')[2] || 'mediciones'
      if (p) this.select(p)
    })
  }
}
</script>
