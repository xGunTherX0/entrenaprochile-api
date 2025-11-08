<template>
  <div class="p-6">
    <button @click="$router.back()" class="mb-4 px-3 py-2 bg-gray-200 rounded">Volver</button>
    <div v-if="loading">Cargando...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>
    <div v-else class="bg-white p-4 rounded shadow">
      <h2 class="text-xl font-bold">{{ rutina.nombre }}</h2>
      <div class="text-sm text-gray-600 mb-2">Por: {{ rutina.entrenador_nombre || '—' }} | Nivel: {{ rutina.nivel }}</div>
      <p class="mb-4">{{ rutina.descripcion }}</p>

      <div class="flex items-center space-x-2 mb-4">
        <button @click="openSolicitar" class="px-3 py-2 bg-blue-600 text-white rounded">Solicitar plan</button>
        <button :disabled="saving || localSaved" @click="follow" class="px-3 py-2 bg-green-600 text-white rounded">{{ saving ? 'Guardando...' : (localSaved ? 'Guardado' : 'Guardar rutina') }}</button>
      </div>

      <div class="border-t pt-4">
        <h3 class="font-semibold mb-2">Plan alimenticio (placeholder)</h3>
        <p>Aquí irá el plan alimenticio asociado. Por ahora se muestra un placeholder.</p>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'
import auth from '../utils/auth.js'

export default {
  name: 'ClienteRutina',
  data() {
    return {
      rutina: null,
      loading: true,
      error: null,
      saving: false,
      localSaved: false
    }
  },
  methods: {
    openSolicitar() {
      // placeholder action
      alert('Funcionalidad de solicitar plan aún no implementada')
    },
    async follow() {
      if (!this.rutina || !this.rutina.id) return
      this.saving = true
      try {
        const res = await api.post(`/api/rutinas/${this.rutina.id}/seguir`, {})
        const body = await res.json()
        if (!res.ok) throw new Error(body.error || 'Error guardando rutina')
        // success: maybe show a small message
        alert('Rutina guardada (servidor)')
        // mark locally as saved as well
        try {
          const saved = JSON.parse(localStorage.getItem('saved_rutinas') || '[]')
          if (!saved.includes(this.rutina.id)) {
            saved.push(this.rutina.id)
            localStorage.setItem('saved_rutinas', JSON.stringify(saved))
          }
          this.localSaved = true
        } catch (e) {}
      } catch (err) {
        console.error('follow rutina', err)
        // fallback: save locally
        try {
          const saved = JSON.parse(localStorage.getItem('saved_rutinas') || '[]')
          if (!saved.includes(this.rutina.id)) {
            saved.push(this.rutina.id)
            localStorage.setItem('saved_rutinas', JSON.stringify(saved))
          }
          this.localSaved = true
          alert('Rutina guardada localmente (inicia sesión para sincronizar)')
        } catch (e) {
          console.error('local fallback failed', e)
        }
      } finally {
        this.saving = false
      }
    }
  },
  async mounted() {
    const id = this.$route.params.id
    try {
  const res = await api.get(`/api/rutinas/public/${id}`, { skipAuth: true })
      const body = await res.json()
      if (!res.ok) throw new Error(body.error || 'Error obteniendo rutina')
      this.rutina = body
    } catch (err) {
      this.error = err.message
    } finally {
      this.loading = false
      // set localSaved state
      try {
        const saved = JSON.parse(localStorage.getItem('saved_rutinas') || '[]')
        this.localSaved = Array.isArray(saved) && saved.includes(Number(id))
      } catch (e) {
        this.localSaved = false
      }
    }
  }
}
</script>
