<template>
  <div class="p-6">
    <button @click="$router.back()" class="mb-4 px-3 py-2 bg-gray-200 rounded">Volver</button>
    <div v-if="loading">Cargando...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>
    <div v-else class="bg-white p-4 rounded shadow">
      <h2 class="text-xl font-bold">{{ rutina.nombre }}</h2>
      <div class="text-sm text-gray-600 mb-2">Por: {{ rutina.entrenador_nombre || '—' }} | Nivel: {{ rutina.nivel }}</div>
      <p class="mb-4">{{ rutina.descripcion }}</p>
      <!-- Mostrar secciones descriptivas completas -->
      <div v-if="rutina.objetivo_principal" class="mb-2">
        <strong>Objetivo principal:</strong>
        <div class="text-sm text-gray-700">{{ rutina.objetivo_principal }}</div>
      </div>
      <div v-if="rutina.enfoque_rutina" class="mb-2">
        <strong>Enfoque:</strong>
        <div class="text-sm text-gray-700">{{ rutina.enfoque_rutina }}</div>
      </div>
      <div v-if="rutina.cualidades_clave" class="mb-2">
        <strong>Cualidades clave:</strong>
        <div class="text-sm text-gray-700">{{ rutina.cualidades_clave }}</div>
      </div>
      <div v-if="rutina.duracion_frecuencia" class="mb-2">
        <strong>Duración / Frecuencia:</strong>
        <div class="text-sm text-gray-700">{{ rutina.duracion_frecuencia }}</div>
      </div>
      <div v-if="rutina.material_requerido" class="mb-2">
        <strong>Material requerido:</strong>
        <div class="text-sm text-gray-700">{{ rutina.material_requerido }}</div>
      </div>
      <div v-if="rutina.instrucciones_estructurales" class="mb-2">
        <strong>Instrucciones estructurales:</strong>
        <div class="text-sm text-gray-700">{{ rutina.instrucciones_estructurales }}</div>
      </div>
      <div v-if="rutina.seccion_descripcion" class="mb-2">
        <strong>Sección seleccionada:</strong>
        <div class="text-sm text-gray-700">{{ rutina.seccion_descripcion }}</div>
      </div>
      <div v-if="rutina.link_url" class="flex items-center space-x-3 mb-4">
        <a :href="rutina.link_url" target="_blank" rel="noopener noreferrer" class="px-3 py-2 bg-green-600 text-white rounded">Abrir enlace</a>
        <img :src="`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(rutina.link_url)}`" alt="QR" class="w-24 h-24 border rounded" />
      </div>

      <!-- "Solicitar rutina" button removed per request -->

      <!-- Plan alimenticio placeholder removed per request: show only the rutina -->
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'

export default {
  name: 'ClienteRutina',
  data() {
    return {
      rutina: null,
      loading: true,
      error: null,
      // saving/localSaved removed: this view no longer offers "Solicitar rutina"
    }
  },
  methods: {
    // solicitar removed: this view no longer supports creating solicitudes
  },
  async mounted() {
    const id = this.$route.params.id
    if (!id || id === 'null' || isNaN(Number(id))) {
      this.error = 'ID de rutina inválido'
      this.loading = false
      return
    }

    try {
      const res = await api.get(`/api/rutinas/public/${id}`)
      const body = await res.json()
      if (!res.ok) throw new Error(body.error || 'Error obteniendo rutina')
      this.rutina = body
    } catch (err) {
      this.error = err.message
    } finally {
      this.loading = false
      // no localSaved handling needed any more
    }
  }
}
</script>
