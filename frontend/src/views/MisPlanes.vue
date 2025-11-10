<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-4">Planes Alimenticios</h1>
    <div class="bg-white p-4 rounded shadow">
      <div v-if="loading">Cargando planes...</div>
      <div v-else>
        <h3 class="font-semibold mb-2">Planes Públicos</h3>
        <div v-if="planesPublicos.length===0" class="text-sm text-gray-600 mb-4">No hay planes disponibles.</div>
        <ul class="space-y-2 mb-4">
          <li v-for="p in planesPublicos" :key="p.id" class="p-3 border rounded bg-gray-50">
            <div class="flex justify-between items-center">
              <div>
                <div class="font-semibold">{{ p.nombre }}</div>
                <div class="text-sm text-gray-600">{{ p.descripcion }}</div>
              </div>
              <div class="space-x-2">
                <button @click="openPlanDetail(p.id)" class="px-3 py-1 bg-blue-600 text-white rounded">Ver</button>
                <button @click="solicitarPlan(p.id)" class="px-3 py-1 bg-green-600 text-white rounded">Solicitar plan</button>
              </div>
            </div>
          </li>
        </ul>

        <h3 class="font-semibold mb-2">Mis Solicitudes de Plan</h3>
        <div v-if="misSolicitudes.length===0" class="text-sm text-gray-600">No has solicitado ningún plan aún.</div>
        <ul class="mt-2 space-y-2">
          <li v-for="s in misSolicitudes" :key="s.id" class="p-3 border rounded bg-white">
            <div class="flex justify-between items-start">
              <div>
                <div class="font-semibold">{{ s.rutina_nombre || ('Rutina ' + s.rutina_id) }}</div>
                <div class="text-sm text-gray-600">Estado: {{ s.estado }} — {{ s.creado_en ? new Date(s.creado_en).toLocaleString() : '' }}</div>
                <div v-if="s.nota" class="text-sm mt-1">Nota: {{ s.nota }}</div>
              </div>
              <div>
                <button @click="openPlanFromSolicitud(s)" class="px-3 py-1 bg-blue-600 text-white rounded">Ver plan</button>
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
      planesPublicos: [],
      misSolicitudes: [],
      loading: false
    }
  },
  methods: {
    async fetchPlanes() {
      this.loading = true
      try {
        const rp = await api.get('/api/planes', { skipAuth: true })
        if (rp && rp.ok) this.planesPublicos = await rp.json()
      } catch (e) {
        console.error('fetch planes publicos failed', e)
      } finally {
        this.loading = false
      }
    },
    async fetchSolicitudes() {
      try {
        const r2 = await api.get('/api/solicitudes/mis')
        if (r2 && r2.ok) this.misSolicitudes = await r2.json()
      } catch (e) {
        console.error('fetch mis solicitudes failed', e)
      }
    },
    openPlanDetail(id) {
      if (!id) return
      this.$router.push(`/cliente/plan/${id}`)
    },
    solicitarPlan(planId) {
      // reuse simple flow from ClienteDashboard
      try {
        api.post(`/api/planes/${planId}/solicitar`)
          .then(async res => {
            if (!res.ok) {
              const b = await res.json().catch(()=>({}))
              throw new Error(b.error || 'Error solicitando plan')
            }
            this.fetchSolicitudes()
            try { alert('Solicitud enviada') } catch (e) {}
          })
          .catch(err => { console.error('solicitarPlan failed', err); alert('No se pudo solicitar el plan') })
      } catch (e) {
        console.error(e)
      }
    },
    openPlanFromSolicitud(solicitud) {
      if (!solicitud) return
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
    this.fetchPlanes()
    this.fetchSolicitudes()
  }
}
</script>
