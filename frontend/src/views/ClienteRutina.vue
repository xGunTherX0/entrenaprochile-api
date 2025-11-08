<template>
  <div class="p-6">
    <button @click="$router.back()" class="mb-4 px-3 py-2 bg-gray-200 rounded">Volver</button>
    <div v-if="loading">Cargando...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>
    <div v-else class="bg-white p-4 rounded shadow">
      <h2 class="text-xl font-bold">{{ rutina.nombre }}</h2>
      <div class="text-sm text-gray-600 mb-2">Por: {{ rutina.entrenador_nombre || '—' }} | Nivel: {{ rutina.nivel }}</div>
      <p class="mb-4">{{ rutina.descripcion }}</p>

      <div class="border-t pt-4">
        <h3 class="font-semibold mb-2">Plan alimenticio (placeholder)</h3>
        <p>Aquí irá el plan alimenticio asociado. Por ahora se muestra un placeholder.</p>
        <div class="mt-4">
          <button class="px-3 py-2 bg-green-600 text-white rounded">Solicitar plan</button>
        </div>
      </div>
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
      error: null
    }
  },
  async mounted() {
    const id = this.$route.params.id
    try {
      const res = await api.get(`/api/rutinas/${id}`, { skipAuth: true })
      const body = await res.json()
      if (!res.ok) throw new Error(body.error || 'Error obteniendo rutina')
      this.rutina = body
    } catch (err) {
      this.error = err.message
    } finally {
      this.loading = false
    }
  }
}
</script>
