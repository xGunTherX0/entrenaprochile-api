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
        <div class="bg-white p-4 rounded shadow-sm">(Placeholder para planes)</div>
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
      try { this.$router.push({ path: this.$route.path, hash: `#${panel}` }) } catch (e) {}
      this.activePanel = panel
    },

    async fetchRutinas() {
      const session = auth.getSession()
      if (!session.user_id) return
      try {
        const base = import.meta.env.VITE_API_BASE || 'https://entrenaprochile-api.onrender.com'
        const headers = { ...auth.authHeaders() }
        const res = await fetch(`${base}/api/rutinas/${session.user_id}`, { headers })
        if (!res.ok) throw new Error('error fetching')
        this.rutinas = await res.json()
      } catch (e) {
        console.error('fetchRutinas', e)
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
      const base = import.meta.env.VITE_API_BASE || 'https://entrenaprochile-api.onrender.com'
      const payload = { ...this.form, entrenador_id: session.user_id }
      try {
        const headers = { 'Content-Type': 'application/json', ...auth.authHeaders() }
        const res = await fetch(`${base}/api/rutinas`, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload)
        })
        if (!res.ok) {
          const err = await res.json()
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
  const res = await fetch(`${base}/api/rutinas/${id}`, { method: 'DELETE', headers: auth.authHeaders() })
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
  const headers = { 'Content-Type': 'application/json', ...auth.authHeaders() }
  const res = await fetch(`${base}/api/rutinas/${id}`, { method: 'PUT', headers, body: JSON.stringify(this.editForm) })
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
  },
  mounted() {
    // initialize from hash
    const h = (this.$route && this.$route.hash) ? this.$route.hash.replace('#', '') : ''
    if (h) this.activePanel = h
    if (this.activePanel === 'rutinas') this.fetchRutinas()
    this.$watch(() => this.$route.hash, (newHash) => {
      const panel = (newHash || '').replace('#', '')
      if (panel) this.select(panel)
    })
  }
}
</script>
