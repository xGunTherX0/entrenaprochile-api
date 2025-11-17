<template>
  <div>
    <div class="flex justify-between items-center">
      <h2 class="text-lg font-semibold">Usuarios</h2>
      <button @click="showCreate = true" class="px-3 py-2 bg-green-600 text-white rounded">Crear Usuario</button>
    </div>

    <div class="mt-3 bg-white rounded shadow overflow-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
            <th class="px-6 py-3"></th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="u in users" :key="u.id">
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ u.id }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900"><router-link :to="`/admin/usuarios/${u.id}`" class="text-blue-600 hover:underline">{{ u.email }}</router-link></td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ u.nombre }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ u.role }} <span v-if="u.activo===false" class="text-sm text-red-600">(desactivado)</span></td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <button v-if="u.role !== 'entrenador' && u.role !== 'admin'" @click="promote(u.id)" class="text-indigo-600 hover:text-indigo-900 mr-3">Promover</button>
              <button v-if="u.role === 'entrenador'" @click="demoteToClient(u.id)" class="text-purple-600 hover:text-purple-900 mr-3">Degradar</button>
              <button @click="changeRole(u.id)" class="text-gray-600 hover:text-gray-900 mr-3">Cambiar rol</button>
              <!-- Nuevo botón: desactivar cuenta (soft) -->
              <button v-if="u.activo !== false" @click="deactivate(u.id)" class="text-yellow-600 hover:text-yellow-900 mr-3">Desactivar</button>
              <!-- Botón reactivar para usuarios desactivados -->
              <button v-else @click="reactivate(u.id)" class="text-green-700 hover:text-green-900 mr-3">Reactivar</button>
              <button @click="remove(u.id)" class="text-red-600 hover:text-red-900">Borrar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</div>

    <!-- create modal simple -->
    <div v-if="showCreate" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40">
      <div class="bg-white rounded shadow-lg w-96 p-6">
        <h3 class="text-lg font-semibold mb-3">Crear Usuario</h3>
        <div class="mb-2"><label class="block text-sm">Email</label><input v-model="newUser.email" class="w-full border rounded px-2 py-1" /></div>
        <div class="mb-2"><label class="block text-sm">Nombre</label><input v-model="newUser.nombre" class="w-full border rounded px-2 py-1" /></div>
        <div class="mb-2"><label class="block text-sm">Password</label><input type="password" v-model="newUser.password" class="w-full border rounded px-2 py-1" /></div>
        <div class="mb-4"><label class="block text-sm">Rol</label>
          <select v-model="newUser.role" class="w-full border rounded px-2 py-1">
            <option value="usuario">Usuario</option>
            <option value="cliente">Cliente</option>
            <option value="entrenador">Entrenador</option>
          </select>
        </div>
        <div class="flex justify-end">
          <button @click="closeCreate" class="mr-2 px-3 py-2 border rounded">Cancelar</button>
          <button @click="createUser" :disabled="creating" class="px-3 py-2 bg-blue-600 text-white rounded">{{ creating ? 'Creando...' : 'Crear' }}</button>
        </div>
        <div v-if="createError" class="mt-3 text-sm text-red-600">{{ createError }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import auth from '../../utils/auth.js'
import api from '../../utils/api.js'
export default {
  name: 'AdminUsuarios',
  data() {
    return {
      users: [],
      error: null,
      showCreate: false,
      newUser: { email: '', nombre: '', password: '', role: 'usuario' },
      creating: false,
      createError: null
    }
  },
  methods: {
    async loadUsers() {
      this.error = null
      try {
  const res = await api.get('/api/admin/usuarios')
        if (!res.ok) {
          const txt = await res.json().catch(() => ({}))
          this.error = txt.error || 'Error cargando usuarios'
          return
        }
        this.users = await res.json()
      } catch (e) {
        this.error = e.message || String(e)
      }
    },
    async promote(id) {
      this.error = null
      try {
  const res = await api.post(`/api/admin/usuarios/${id}/promote`, null)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || 'Error promoviendo usuario'
          return
        }
        await this.loadUsers()
        this.$emit('refresh-metrics')
      } catch (e) {
        this.error = e.message || String(e)
      }
    },
    async remove(id) {
      this.error = null
      // Ask admin whether to soft-disable (default) or hard-delete
      const soft = confirm('¿Deseas DESACTIVAR la cuenta en vez de eliminarla permanentemente?\nAceptar = Desactivar (recomendado), Cancelar = Eliminar permanentemente')
      if (!confirm('¿Confirmar la acción seleccionada?')) return
      const mode = soft ? 'soft' : 'hard'
      try {
  const res = await api.del(`/api/admin/usuarios/${id}?mode=${mode}`)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || 'Error borrando usuario'
          return
        }
        await this.loadUsers()
        this.$emit('refresh-metrics')
      } catch (e) {
        this.error = e.message || String(e)
      }
    },
    async changeRole(id) {
      this.error = null
      const newRole = prompt("Indica el rol deseado para el usuario (cliente / entrenador / usuario):")
      if (!newRole) return
      const r = newRole.trim().toLowerCase()
      if (!['cliente', 'entrenador', 'usuario'].includes(r)) {
        alert('Rol inválido')
        return
      }
      if (!confirm(`Confirmar cambiar rol a: ${r}?`)) return
      try {
        const res = await api.post(`/api/admin/usuarios/${id}/set_role`, { role: r })
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || 'Error cambiando rol'
          return
        }
        await this.loadUsers()
        this.$emit('refresh-metrics')
      } catch (e) {
        this.error = e.message || String(e)
      }
    },
    async demoteToClient(id) {
      this.error = null
      if (!confirm('Confirmar degradar este entrenador a cliente?')) return
      try {
        const res = await api.post(`/api/admin/usuarios/${id}/set_role`, { role: 'cliente' })
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || 'Error degradando usuario'
          return
        }
        await this.loadUsers()
        this.$emit('refresh-metrics')
      } catch (e) {
        this.error = e.message || String(e)
      }
    },
    async deactivate(id) {
      // Soft-disable a user quickly
      this.error = null
      if (!confirm('¿Confirmar DESACTIVAR la cuenta de este usuario? (esto hará que su contenido deje de ser público)')) return
      try {
        const res = await api.del(`/api/admin/usuarios/${id}?mode=soft`)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || 'Error desactivando usuario'
          return
        }
        await this.loadUsers()
        this.$emit('refresh-metrics')
      } catch (e) {
        this.error = e.message || String(e)
      }
    },
    async reactivate(id) {
      this.error = null
      if (!confirm('¿Confirmar REACTIVAR la cuenta de este usuario?')) return
      try {
        const res = await api.post(`/api/admin/usuarios/${id}/reactivar`, null)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || 'Error reactivando usuario'
          return
        }
        await this.loadUsers()
        this.$emit('refresh-metrics')
      } catch (e) {
        this.error = e.message || String(e)
      }
    },
    closeCreate() {
      this.showCreate = false
      this.createError = null
      this.newUser = { email: '', nombre: '', password: '', role: 'usuario' }
      this.creating = false
    },
    async createUser() {
      this.createError = null
      if (!this.newUser.email || !this.newUser.password) {
        this.createError = 'Email y password son obligatorios'
        return
      }
      this.creating = true
      try {
        const payload = { email: this.newUser.email, nombre: this.newUser.nombre || this.newUser.email, password: this.newUser.password }
  const res = await api.post('/api/usuarios/register', payload, { skipAuth: true })
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.createError = j.error || j.message || `Error creando usuario (${res.status})`
          return
        }
        const body = await res.json()
        const newId = body.id
        if (this.newUser.role === 'cliente') {
          const r2 = await api.post(`/api/admin/usuarios/${newId}/create_cliente`, null)
          if (!r2.ok) {
            const j2 = await r2.json().catch(() => ({}))
            this.createError = `Usuario creado pero fallo al crear cliente: ${j2.error || j2.detail || r2.status}`
          }
        } else if (this.newUser.role === 'entrenador') {
          const r3 = await api.post(`/api/admin/usuarios/${newId}/promote`, null)
          if (!r3.ok) {
            const j3 = await r3.json().catch(() => ({}))
            this.createError = `Usuario creado pero fallo al crear entrenador: ${j3.error || j3.detail || r3.status}`
          }
        }
        await this.loadUsers()
        if (!this.createError) this.closeCreate()
        this.$emit('refresh-metrics')
      } catch (e) {
        this.createError = e.message || String(e)
      } finally {
        this.creating = false
      }
    }
  },
  mounted() {
    this.loadUsers()
  }
}
</script>
