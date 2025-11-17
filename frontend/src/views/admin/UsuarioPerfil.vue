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
        <button v-if="canEditRoles" @click="openChangeRole" class="px-3 py-2 border rounded">Cambiar rol</button>
      </div>

      <!-- modal para cambiar rol simple -->
      <div v-if="showRoleModal" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40">
        <div class="bg-white rounded shadow-lg w-80 p-4">
          <h3 class="text-lg font-semibold mb-2">Cambiar rol</h3>
          <select v-model="selectedRole" class="w-full border rounded px-2 py-1 mb-3">
            <option value="cliente">Cliente</option>
            <option value="entrenador">Entrenador</option>
            <option value="usuario">Usuario</option>
          </select>
          <div class="flex justify-end">
            <button @click="closeRoleModal" class="mr-2 px-3 py-2 border rounded">Cancelar</button>
            <button @click="submitRole" class="px-3 py-2 bg-blue-600 text-white rounded">Guardar</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../utils/api.js'
import auth from '../../utils/auth.js'
export default {
  name: 'UsuarioPerfil',
  props: ['id'],
  data() {
    return { profile: null, loading: true, error: null, showRoleModal: false, selectedRole: 'usuario' }
  },
  computed: {
    canEditRoles() {
      const role = auth.getRole()
      return role === 'admin'
    }
  },
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
    },
    openChangeRole() {
      this.selectedRole = (this.profile.roles && this.profile.roles.includes('entrenador')) ? 'entrenador' : (this.profile.roles.includes('cliente') ? 'cliente' : 'usuario')
      this.showRoleModal = true
    },
    closeRoleModal() { this.showRoleModal = false },
    async submitRole() {
      try {
        const res = await api.post(`/api/admin/usuarios/${this.profile.id}/set_role`, { role: this.selectedRole })
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          alert(j.error || 'Error cambiando rol')
          return
        }
        this.showRoleModal = false
        await this.load()
        this.$root.$emit('refresh-metrics')
      } catch (e) {
        alert(e.message || String(e))
      }
    }
  },
  mounted() {
    this.load()
  }
}
</script>
