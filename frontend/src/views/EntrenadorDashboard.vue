<template>
  <div class="min-h-screen flex bg-gray-50">
    <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Entrenador</h2>
      <ul>
        <li class="mb-2"><button @click="select('rutinas')" :class="{'text-blue-600 font-semibold': activePanel==='rutinas'}" class="text-left w-full">Mis Rutinas</button></li>
        <li class="mb-2"><button @click="select('planes')" :class="{'text-blue-600 font-semibold': activePanel==='planes'}" class="text-left w-full">Mis Planes Alimenticios</button></li>
        <li class="mb-2"><button @click="select('publicar')" :class="{'text-blue-600 font-semibold': activePanel==='publicar'}" class="text-left w-full">Publicar Contenido</button></li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>
    <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold">Entrenador Dashboard</h1>

      <section v-if="activePanel === 'rutinas'" class="mt-4">
        <h2 class="text-xl font-semibold mb-2">Crear nueva Rutina</h2>
        <form @submit.prevent="createRutina" class="space-y-3 bg-white p-4 rounded shadow-sm max-w-lg">
          <div>
            <label class="block text-sm font-medium">Nombre</label>
            <input v-model="form.nombre" class="mt-1 block w-full border rounded px-2 py-1" required />
          </div>
          <div>
            <label class="block text-sm font-medium">Descripción</label>
            <textarea v-model="form.descripcion" class="mt-1 block w-full border rounded px-2 py-1"></textarea>
          </div>
          <div>
            <label class="block text-sm font-medium">Nivel</label>
            <select v-model="form.nivel" class="mt-1 block w-full border rounded px-2 py-1">
              <option value="Básico">Básico</option>
              <option value="Intermedio">Intermedio</option>
              <option value="Avanzado">Avanzado</option>
            </select>
          </div>
          <div class="flex items-center">
            <input type="checkbox" v-model="form.es_publica" id="publica" />
            <label for="publica" class="ml-2 text-sm">Es pública</label>
          </div>
          <div>
            <button type="submit" class="px-3 py-2 bg-green-600 text-white rounded">Crear Rutina</button>
          </div>
        </form>

  <h2 class="text-xl font-semibold mt-6 mb-2">Mis Rutinas</h2>
        <div class="bg-white p-4 rounded shadow-sm">
          <table class="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th class="px-4 py-2 text-left">Nombre</th>
                <th class="px-4 py-2 text-left">Nivel</th>
                <th class="px-4 py-2 text-left">Pública</th>
                <th class="px-4 py-2 text-left">Creado</th>
                <th class="px-4 py-2 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rutinas" :key="r.id" class="border-t">
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id">{{ r.nombre }}</div>
                  <div v-else>
                    <input v-model="editForm.nombre" class="border px-2 py-1 w-full" />
                  </div>
                </td>
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id">{{ r.nivel }}</div>
                  <div v-else>
                    <select v-model="editForm.nivel" class="border px-2 py-1">
                      <option value="Básico">Básico</option>
                      <option value="Intermedio">Intermedio</option>
                      <option value="Avanzado">Avanzado</option>
                    </select>
                  </div>
                </td>
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id">{{ r.es_publica ? 'Sí' : 'No' }}</div>
                  <div v-else>
                    <input type="checkbox" v-model="editForm.es_publica" />
                  </div>
                </td>
                <td class="px-4 py-2">{{ formatDate(r.creado_en) }}</td>
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id" class="space-x-2">
                    <button @click="startEdit(r)" class="px-2 py-1 bg-yellow-400 text-white rounded">Editar</button>
                    <button @click="deleteRutina(r.id)" class="px-2 py-1 bg-red-600 text-white rounded">Eliminar</button>
                  </div>
                  <div v-else class="space-x-2">
                    <button @click="saveEdit(r.id)" class="px-2 py-1 bg-green-600 text-white rounded">Guardar</button>
                    <button @click="cancelEdit" class="px-2 py-1 bg-gray-300 rounded">Cancelar</button>
                  </div>
                </td>
              </tr>
              <tr v-if="!rutinas.length">
                <td class="px-4 py-2" colspan="5">No hay rutinas aún.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-if="activePanel === 'planes'" class="mt-4">
        <h2 class="text-xl font-semibold">Mis Planes Alimenticios</h2>
        <div class="bg-white p-4 rounded shadow-sm max-w-xl">
          <form @submit.prevent="createPlan" class="space-y-3">
            <div>
              <label class="block text-sm font-medium">Nombre</label>
              <input v-model="planForm.nombre" class="mt-1 block w-full border rounded px-2 py-1" required />
            </div>
            <div>
              <label class="block text-sm font-medium">Descripción</label>
              <textarea v-model="planForm.descripcion" class="mt-1 block w-full border rounded px-2 py-1"></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium">Contenido</label>
              <textarea v-model="planForm.contenido" class="mt-1 block w-full border rounded px-2 py-1" placeholder="Ej: Desayuno, Almuerzo, Cena"></textarea>
            </div>
            <div class="flex items-center">
              <input type="checkbox" v-model="planForm.es_publico" id="publico-plan" />
              <label for="publico-plan" class="ml-2 text-sm">Es público</label>
            </div>
            <div>
              <button type="submit" class="px-3 py-2 bg-green-600 text-white rounded">Crear Plan</button>
            </div>
          </form>

          <h3 class="text-lg font-semibold mt-6">Tus planes</h3>
          <div v-if="misPlanes.length" class="mt-2 space-y-3">
            <div v-for="p in misPlanes" :key="p.id" class="border rounded p-3 bg-gray-50">
              <div class="flex justify-between items-start">
                <div>
                  <div class="font-semibold">{{ p.nombre }}</div>
                  <div class="text-sm text-gray-600">{{ formatDate(p.creado_en) }}</div>
                </div>
                <div class="text-right text-sm">
                  <div>{{ p.es_publico ? 'Público' : 'Privado' }}</div>
                </div>
              </div>
              <div class="mt-2 text-sm text-gray-700">{{ p.descripcion }}</div>
              <div class="mt-2 text-xs text-gray-600">{{ p.contenido }}</div>
            </div>
          </div>
          <div v-else class="mt-2 text-sm text-gray-600">No hay planes aún.</div>
        </div>
      </section>

      <section v-if="activePanel === 'publicar'" class="mt-4">
        <h2 class="text-xl font-semibold">Publicar Contenido</h2>
        <div class="bg-white p-4 rounded shadow-sm">(Placeholder para publicar contenido)</div>
      </section>
    </main>
  </div>
</template>

<script>
import auth from '../utils/auth.js'
import api from '../utils/api.js'

export default {
  name: 'EntrenadorDashboard',
  data() {
    return {
      form: {
        nombre: '',
        descripcion: '',
        nivel: 'Básico',
        es_publica: false
      },
      rutinas: []
      ,
      activePanel: 'rutinas'
    }
  },
  methods: {
    logout() {
      auth.clearSession()
      this.$router.push('/')
    },

    select(panel) {
      try { this.$router.push(`/entrenador/${panel}`) } catch (e) {}
      this.activePanel = panel
    },

    async fetchRutinas() {
      const session = auth.getSession()
      if (!session.user_id) return
      try {
        const res = await api.get(`/api/rutinas/${session.user_id}`)
        if (!res.ok) throw new Error('error fetching')
        this.rutinas = await res.json()
      } catch (e) {
        console.error('fetchRutinas', e)
      }
    },

    async fetchMisPlanes() {
      try {
        const res = await api.get('/api/planes/mis')
        if (!res.ok) {
          // could be 403 if not entrenador
          return
        }
        const j = await res.json()
        this.misPlanes = Array.isArray(j) ? j : []
      } catch (e) {
        console.error('fetchMisPlanes', e)
      }
    },

    async createPlan() {
      const session = auth.getSession()
      if (!session || !session.user_id) {
        alert('No autenticado')
        return
      }
      try {
        const payload = { ...this.planForm }
        const res = await api.post('/api/planes', payload)
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          // Mostrar el detalle completo del error para depuración (incluye received_keys/raw_body_length)
          console.error('createPlan error detail:', err)
          alert('Error creando plan (ver consola para detalle)\n' + JSON.stringify(err))
          return
        }
        // reset form and refresh list
        this.planForm = { nombre: '', descripcion: '', contenido: '', es_publico: false }
        await this.fetchMisPlanes()
      } catch (e) {
        console.error('createPlan', e)
        alert('Error creando plan')
      }
    },

    formatDate(iso) {
      try { return new Date(iso).toLocaleString() } catch { return iso }
    },

    async createRutina() {
      const session = auth.getSession()
      if (!session.user_id) {
        alert('No autenticado')
        return
      }
      const payload = { ...this.form, entrenador_id: session.user_id }
      try {
        const res = await api.post('/api/rutinas', payload)
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          alert('Error: ' + (err.error || JSON.stringify(err)))
          return
        }
        this.form.nombre = ''
        this.form.descripcion = ''
        this.form.nivel = 'Básico'
        this.form.es_publica = false
        await this.fetchRutinas()
      } catch (e) {
        console.error('createRutina', e)
        alert('Error creando rutina')
      }
    },

    // Edit/Delete handlers
    async deleteRutina(id) {
      if (!confirm('¿Eliminar rutina?')) return
      const session = auth.getSession()
      try {
        const res = await api.del(`/api/rutinas/${id}`)
        if (!res.ok) {
          const err = await res.json()
          alert('Error: ' + (err.error || JSON.stringify(err)))
          return
        }
        await this.fetchRutinas()
      } catch (e) {
        console.error('deleteRutina', e)
        alert('Error eliminando rutina')
      }
    },

    startEdit(r) {
      this.editingId = r.id
      this.editForm = { nombre: r.nombre, nivel: r.nivel, es_publica: !!r.es_publica }
    },

    cancelEdit() {
      this.editingId = null
      this.editForm = { nombre: '', nivel: 'Básico', es_publica: false }
    },

    async saveEdit(id) {
      const session = auth.getSession()
      try {
        const res = await api.put(`/api/rutinas/${id}`, this.editForm)
        if (!res.ok) {
          const err = await res.json()
          alert('Error: ' + (err.error || JSON.stringify(err)))
          return
        }
        this.cancelEdit()
        await this.fetchRutinas()
      } catch (e) {
        console.error('saveEdit', e)
        alert('Error actualizando rutina')
      }
    }
  },
  created() {
    this.editingId = null
    this.editForm = { nombre: '', nivel: 'Básico', es_publica: false }
    // plan form state
    this.planForm = { nombre: '', descripcion: '', contenido: '', es_publico: false }
    this.misPlanes = []
  },
  mounted() {
    // initialize from route path (e.g. /entrenador/rutinas)
    const parts = (this.$route && this.$route.path) ? this.$route.path.split('/') : []
    const panel = parts[2] || 'rutinas'
    if (panel) this.activePanel = panel
    if (this.activePanel === 'rutinas') this.fetchRutinas()
    if (this.activePanel === 'planes') this.fetchMisPlanes()
    this.$watch(() => this.$route.path, (newPath) => {
      const p = (newPath || '').split('/')[2] || 'rutinas'
      if (p) this.select(p)
    })
  }
}
</script>
