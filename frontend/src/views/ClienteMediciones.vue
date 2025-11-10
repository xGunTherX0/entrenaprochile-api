<template>
  <div>
    <h1 class="text-2xl font-bold">Registro de Mediciones</h1>

    <div class="mt-4 max-w-md bg-white p-4 rounded shadow">
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

    <div class="mt-8 bg-white p-4 rounded shadow">
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
    </div>

    <div class="mt-8 bg-white p-4 rounded shadow">
      <h2 class="text-lg font-semibold mb-2">Evolución de Peso</h2>
      <WeightChart :measurements="mediciones" />
    </div>
  </div>
</template>

<script>
import WeightChart from '../components/WeightChart.vue'
import api from '../utils/api.js'
import auth from '../utils/auth.js'

export default {
  name: 'ClienteMediciones',
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
    }
  },
  methods: {
    async submitMedicion() {
      this.saving = true
      this.msg = ''
      try {
        const res = await api.post('/api/mediciones', { peso: this.peso, altura: this.altura, cintura: this.cintura })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Error al guardar')
        this.msg = 'Medición guardada con id ' + data.id
        this.peso = this.altura = this.cintura = null
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
    }
  },
  mounted() {
    this.fetchMediciones()
  }
}
</script>

<style scoped>
</style>
