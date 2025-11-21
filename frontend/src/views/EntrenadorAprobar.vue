<template>
  <div class="text-gray-800">
    <h2 class="text-lg font-semibold text-indigo-800">Solicitudes pendientes</h2>
    <div class="mt-3 bg-white rounded shadow p-4 text-gray-800">
      <div v-if="loading">Cargando solicitudes pendientes...</div>
      <div v-else>
        <div v-if="solicitudes.length === 0" class="text-sm text-gray-700">No hay solicitudes pendientes.</div>
        <ul>
          <li v-for="s in solicitudes" :key="s.id" class="p-3 border rounded bg-gray-50 mb-2">
            <div class="flex justify-between items-start">
              <div>
                <div class="font-semibold text-indigo-800">{{ s.rutina_nombre || 'Sin nombre' }}</div>
                <div class="text-sm text-gray-700">ID: {{ s.id }} — Estado: <span :class="estadoClass(s.estado)">{{ s.estado }}</span></div>
                <div v-if="s.nota" class="mt-1 text-sm text-gray-700">Nota: {{ s.nota }}</div>
                <div v-if="s.creado_en" class="mt-1 text-xs text-gray-600">Creado: {{ s.creado_en }}</div>
              </div>
              <div class="space-x-2">
                <button v-if="s.estado !== 'aceptado'" @click="updateEstado(s.id, 'aceptado')" class="px-3 py-1 bg-green-600 text-white rounded">Aceptar</button>
                <button v-if="s.estado !== 'rechazado'" @click="updateEstado(s.id, 'rechazado')" class="px-3 py-1 bg-red-500 text-white rounded">Rechazar</button>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../utils/api'
import toast from '../utils/toast'

export default {
  name: 'EntrenadorAprobar',
  data() {
    return {
      solicitudes: [],
      loading: false
    }
  },
  mounted() {
    this.fetchSolicitudes()
  },
  methods: {
    async fetchSolicitudes() {
      this.loading = true
      try {
        const res = await api.get('/api/solicitudes/pendientes')
        if (res && res.status === 200) {
          const j = await res.json()
          this.solicitudes = j || []
        } else {
          toast.show('Error obteniendo solicitudes pendientes', 3000)
        }
      } catch (e) {
        console.error(e)
        toast.show('Error de red al obtener solicitudes', 3000)
      } finally {
        this.loading = false
      }
    },
    estadoClass(e) {
      if (!e) return 'text-gray-600'
      if (e === 'aceptado' || e === 'aceptada') return 'text-green-600'
      if (e === 'rechazado' || e === 'rechazada' || e === 'cancelado') return 'text-red-600'
      return 'text-yellow-600'
    },
    async updateEstado(id, estado) {
      try {
        const res = await api.put(`/api/solicitudes/${id}`, { estado })
        if (res && res.status === 200) {
          toast.show('Solicitud actualizada', 2000)
          // refresh list
          this.fetchSolicitudes()
        } else {
          const text = res ? await res.text() : 'sin respuesta'
          toast.show('Error actualizando solicitud: ' + text, 4000)
        }
      } catch (e) {
        console.error(e)
        toast.show('Error de red al actualizar solicitud', 3000)
      }
    }
  }
}
</script>
