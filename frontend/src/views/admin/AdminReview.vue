<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">Revisión de Contenido (Rutinas y Planes)</h2>

    <div class="mb-6">
      <h3 class="font-semibold">Rutinas no publicadas</h3>
      <div v-if="loadingR">Cargando...</div>
      <div v-if="!loadingR && rutinas.length===0" class="text-sm text-gray-600">No hay rutinas pendientes.</div>
      <div v-for="r in rutinas" :key="'r-'+r.id" class="border p-3 rounded mb-2 bg-white">
        <div class="flex justify-between items-start">
          <div>
            <div class="font-semibold">{{ r.nombre }} <small class="text-xs text-gray-500">(id: {{ r.id }})</small></div>
            <div class="text-sm text-gray-700">{{ r.descripcion }}</div>
            <div class="text-xs text-gray-500">Entrenador: {{ r.entrenador_nombre || r.entrenador_usuario_id }} — Nivel: {{ r.nivel }}</div>
          </div>
          <div class="space-x-2">
            <button @click="approveRutina(r.id)" class="px-2 py-1 bg-green-600 text-white rounded text-sm">Aprobar</button>
            <button @click="rejectRutina(r.id)" class="px-2 py-1 bg-red-600 text-white rounded text-sm">Rechazar</button>
          </div>
        </div>
      </div>
    </div>

    <div>
      <h3 class="font-semibold">Planes no publicados</h3>
      <div v-if="loadingP">Cargando...</div>
      <div v-if="!loadingP && planes.length===0" class="text-sm text-gray-600">No hay planes pendientes.</div>
      <div v-for="p in planes" :key="'p-'+p.id" class="border p-3 rounded mb-2 bg-white">
        <div class="flex justify-between items-start">
          <div>
            <div class="font-semibold">{{ p.nombre }} <small class="text-xs text-gray-500">(id: {{ p.id }})</small></div>
            <div class="text-sm text-gray-700">{{ p.descripcion }}</div>
            <div class="text-xs text-gray-500">Entrenador: {{ p.entrenador_nombre || p.entrenador_usuario_id }}</div>
          </div>
          <div class="space-x-2">
            <button @click="approvePlan(p.id)" class="px-2 py-1 bg-green-600 text-white rounded text-sm">Aprobar</button>
            <button @click="rejectPlan(p.id)" class="px-2 py-1 bg-red-600 text-white rounded text-sm">Rechazar</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../utils/api.js'
export default {
  name: 'AdminReview',
  data() {
    return {
      rutinas: [],
      planes: [],
      loadingR: false,
      loadingP: false,
      error: null
    }
  },
  mounted() {
    this.loadAll()
  },
  methods: {
    async loadAll() {
      this.error = null
      this.loadingR = true
      this.loadingP = true
      try {
        const res = await api.get('/api/admin/review')
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || 'Error cargando elementos pendientes'
          this.rutinas = []
          this.planes = []
          this.loadingR = false
          this.loadingP = false
          return
        }
        const body = await res.json()
        this.rutinas = body.rutinas || []
        this.planes = body.planes || []
      } catch (e) {
        this.error = e.message || String(e)
        this.rutinas = []
        this.planes = []
      } finally {
        this.loadingR = false
        this.loadingP = false
      }
    },
    async approveRutina(id) {
      if (!confirm('Aprobar rutina y publicarla?')) return
      try {
        const res = await api.post(`/api/admin/review/rutina/${id}/approve`, null)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          alert(j.error || 'Error aprobando')
          return
        }
        await this.loadAll()
      } catch (e) { alert(e.message || String(e)) }
    },
    async rejectRutina(id) {
      if (!confirm('Rechazar rutina (se eliminará)?')) return
      try {
        const res = await api.post(`/api/admin/review/rutina/${id}/reject`, null)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          alert(j.error || 'Error rechazando')
          return
        }
        await this.loadAll()
      } catch (e) { alert(e.message || String(e)) }
    },
    async approvePlan(id) {
      if (!confirm('Aprobar plan y publicarlo?')) return
      try {
        const res = await api.post(`/api/admin/review/plan/${id}/approve`, null)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          alert(j.error || 'Error aprobando')
          return
        }
        await this.loadAll()
      } catch (e) { alert(e.message || String(e)) }
    },
    async rejectPlan(id) {
      if (!confirm('Rechazar plan (se eliminará)?')) return
      try {
        const res = await api.post(`/api/admin/review/plan/${id}/reject`, null)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          alert(j.error || 'Error rechazando')
          return
        }
        await this.loadAll()
      } catch (e) { alert(e.message || String(e)) }
    }
  }
}
</script>
