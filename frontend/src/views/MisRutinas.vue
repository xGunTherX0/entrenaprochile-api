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
            <li v-for="r in filteredRutinas" :key="r.id" class="p-3 border rounded bg-white">
              <div class="flex justify-between items-start">
                <div @click="toggleExpand(r.id)" class="cursor-pointer">
                  <div class="font-semibold">{{ r.nombre }}</div>
                  <div class="text-sm text-gray-600">{{ r.descripcion }}</div>
                  <div v-if="r.solicitud_id" class="text-sm text-yellow-700">Estado: {{ r.estado || 'pendiente' }}</div>
                </div>
                <div class="space-x-2">
                    <button
                      :disabled="!canView(r)"
                      @click="openRutinaDetail(r.real_rutina_id || r.id)"
                      :title="canView(r) ? 'Ver' : 'El entrenador no ha autorizado ver esta rutina'"
                      class="px-3 py-1 rounded"
                      :class="canView(r) ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600 cursor-not-allowed'"
                    >
                      Ver
                    </button>
                  <button v-if="r.solicitud_id" @click="cancelSolicitud(r.solicitud_id)" class="px-3 py-1 bg-red-600 text-white rounded">Cancelar solicitud</button>
                  <button v-else @click="unfollowRutina(r.id)" class="px-3 py-1 bg-red-600 text-white rounded">Eliminar</button>
                </div>
              </div>
              <div v-if="isExpanded(r.id)" class="mt-3 p-3 bg-gray-50 rounded text-sm text-gray-700">
                <div v-if="r.objetivo_principal"><strong>Objetivo principal:</strong> {{ r.objetivo_principal }}</div>
                <div v-if="r.enfoque_rutina"><strong>Enfoque:</strong> {{ r.enfoque_rutina }}</div>
                <div v-if="r.cualidades_clave"><strong>Cualidades clave:</strong> {{ r.cualidades_clave }}</div>
                <div v-if="r.duracion_frecuencia"><strong>Duración / Frecuencia:</strong> {{ r.duracion_frecuencia }}</div>
                <div v-if="r.material_requerido"><strong>Material requerido:</strong> {{ r.material_requerido }}</div>
                <div v-if="r.instrucciones_estructurales"><strong>Instrucciones:</strong> {{ r.instrucciones_estructurales }}</div>
                <div v-if="r.seccion_descripcion"><strong>Descripción:</strong> {{ r.seccion_descripcion }}</div>
                <div v-if="r.nivel"><strong>Nivel:</strong> {{ r.nivel }}</div>
                <div v-if="r.link_url"><strong>Link:</strong> <a :href="r.link_url" target="_blank" class="text-blue-600">{{ r.link_url }}</a></div>
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
      localSavedRutinas: [],
      expanded: {}
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
        // also load solicitudes pendientes and merge rutina-type solicitudes
        try {
          const r2 = await api.get('/api/solicitudes/mis')
          if (r2 && r2.ok) {
            const all = await r2.json()
            const rutinaSolicitudes = Array.isArray(all) ? all.filter(s => s && (() => { const rid = Number(s.rutina_id); return !isNaN(rid) && rid > 0 })()) : []
            // Merge rutina-type solicitudes but avoid creating multiple placeholders
            // for the same rutina_id (can happen if multiple solicitudes exist).
            for (let i = 0; i < rutinaSolicitudes.length; i++) {
              const s = rutinaSolicitudes[i]
              // if rutina already present (accepted/saved) or a placeholder for the
              // same rutina_id already exists, skip
              const targetRutinaId = Number(s.rutina_id)
              if (isNaN(targetRutinaId) || targetRutinaId <= 0) continue
              const exists = this.misRutinas.find(r => {
                const rid = Number(r.real_rutina_id || r.id)
                return !isNaN(rid) && rid === targetRutinaId
              })
              if (exists) continue
              // push a single placeholder entry representing the solicitud
              this.misRutinas.push({ id: `solicitud-${s.id}`, real_rutina_id: s.rutina_id, nombre: s.rutina_nombre || ('Rutina ' + s.rutina_id), descripcion: s.nota || '', solicitud_id: s.id, estado: s.estado || 'pendiente' })
            }
          }
        } catch (e) {
          console.error('fetch solicitudes for mis rutinas failed', e)
        }
        // Merge any locally-saved rutina ids (fallback when server save failed)
        try {
          const saved = JSON.parse(localStorage.getItem('saved_rutinas') || '[]')
          this.localSavedRutinas = Array.isArray(saved) ? saved : []
        } catch (e) {
          this.localSavedRutinas = []
        }
        // Do not add local-only placeholders; only show server-synced saved rutinas.
        // Detailed rutina fetch removed: details are shown on the detail view (ClienteRutina)
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
    ,
    async cancelSolicitud(solicitudId) {
      if (!solicitudId) return
      if (!confirm('¿Seguro que quieres cancelar esta solicitud?')) return
      try {
        const res = await api.del(`/api/solicitudes/${solicitudId}`)
        if (res && res.ok) {
          this.misRutinas = (this.misRutinas || []).filter(item => item.solicitud_id !== solicitudId)
          try { alert('Solicitud cancelada') } catch (e) {}
        } else {
          const b = await res.json().catch(()=>({}));
          throw new Error(b.error || 'Error cancelando solicitud')
        }
      } catch (e) {
        console.error('cancelSolicitud failed', e)
        try { alert('No se pudo cancelar la solicitud: ' + (e.message || e)) } catch (ee) {}
      }
    }
    ,
    toggleExpand(id) {
      // keep reactive by replacing the object
      this.expanded = Object.assign({}, this.expanded, { [id]: !this.expanded[id] })
    },
    isExpanded(id) {
      return !!this.expanded[id]
    }
    ,
    canView(r) {
      // If the item represents a solicitud, only allow viewing when accepted
      try {
        if (!r) return false
        if (r.solicitud_id) {
          const estado = (r.estado || '').toString().toLowerCase()
          return estado === 'aceptado' || estado === 'accepted'
        }
        // otherwise allow (saved rutina or normal)
        return true
      } catch (e) {
        return false
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
