<template>
  <div>
    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold">Perfil de usuario</h2>
      <button @click="$router.back()" class="px-3 py-2 border rounded">Volver</button>
    </div>

    <div v-if="loading" class="mt-4 text-gray-500">Cargando perfil...</div>
    <div v-else-if="error" class="mt-4 text-red-600">{{ error }}</div>

    <div v-else class="mt-4 bg-white rounded shadow p-6">
      <div class="mb-4">
        <div class="text-sm text-gray-500">Nombre</div>
        <div class="text-xl font-bold">{{ profile.nombre }}</div>
      </div>
      <div class="mb-4">
        <div class="text-sm text-gray-500">Email</div>
        <div class="text-sm"><a :href="`mailto:${profile.email}`" class="text-blue-600 hover:underline">{{ profile.email }}</a></div>
      </div>
      <div class="mb-4">
        <div class="text-sm text-gray-500">Roles</div>
        <div class="text-sm">{{ profile.roles.join(', ') || 'usuario' }}</div>
      </div>
      <div v-if="profile.entrenador" class="mb-4">
        <div class="text-sm text-gray-500">Especialidad</div>
        <div class="text-sm">{{ profile.entrenador.speciality || '—' }}</div>
      </div>
      <div v-if="profile.rutinas && profile.rutinas.length" class="mb-4">
        <div class="text-sm text-gray-500">Rutinas (últimas)</div>
        <ul class="list-disc pl-5 text-sm">
          <li v-for="r in profile.rutinas" :key="r.id">{{ r.nombre }}</li>
        </ul>
      </div>

      <div class="mt-6">
        <button @click="contact" class="px-3 py-2 bg-green-600 text-white rounded mr-2">Contactar por email</button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../utils/api.js'
export default {
  name: 'UsuarioPerfil',
  props: ['id'],
  data() {
    return { profile: null, loading: true, error: null }
  },
  computed: {},
  methods: {
    async load() {
      this.loading = true
      this.error = null
      try {
        const res = await api.get(`/api/usuarios/${this.id}`)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || `Error cargando perfil (${res.status})`
          return
        }
        this.profile = await res.json()
      } catch (e) {
        this.error = e.message || String(e)
      } finally {
        this.loading = false
      }
    },
    contact() {
      if (this.profile && this.profile.email) window.location.href = `mailto:${this.profile.email}`
    }
  },
  mounted() {
    this.load()
  }
}
</script>
