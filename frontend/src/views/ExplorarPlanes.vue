<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Explorar Planes Nutricionales</h1>
    <div class="bg-white p-4 rounded shadow">
      <div v-if="loading">Cargando planes...</div>
      <div v-else>
        <div v-if="planes.length===0" class="text-sm text-gray-600">No hay planes públicos disponibles.</div>
        <ul class="space-y-2">
          <li v-for="p in planes" :key="p.id" class="p-3 border rounded bg-gray-50 flex justify-between items-center">
            <div>
              <div class="font-semibold">{{ p.nombre }}</div>
              <div class="text-sm text-gray-600">{{ p.descripcion }}</div>
            </div>
            <div class="space-x-2">
              <button @click="openPlanDetail(p.id)" class="px-3 py-1 bg-blue-600 text-white rounded">Ver</button>
              <button @click="elegirPlan(p.id)" :disabled="loadingIds.includes(p.id)" class="px-3 py-1 bg-green-600 text-white rounded">{{ loadingIds.includes(p.id) ? 'Elegiendo...' : 'Elegir plan' }}</button>
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
  name: 'ExplorarPlanes',
  data() {
    return {
      planes: [],
      loading: false,
      loadingIds: []
    }
  },
  methods: {
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
    openPlanDetail(id) {
      if (!id) return
      this.$router.push(`/cliente/plan/${id}`)
    },
    async elegirPlan(planId) {
      if (!planId) return
      if (!this.loadingIds.includes(planId)) this.loadingIds.push(planId)
      try {
        const res = await api.post(`/api/planes/${planId}/solicitar`)
        if (res && res.ok) {
          // go to Mis Planes screen where solicitudes are listed
          this.$router.push('/cliente/planes')
        } else {
          const b = await res.json().catch(()=>({}));
          throw new Error(b.error || 'Error al elegir plan')
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
  }
}
</script>

<style scoped>
</style>
