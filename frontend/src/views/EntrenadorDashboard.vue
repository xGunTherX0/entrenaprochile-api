<template>
  <div class="min-h-screen flex bg-gray-50">
    <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Entrenador</h2>
      <ul>
        <li class="mb-2"><a href="#" class="text-blue-600">Mis Rutinas</a></li>
        <li class="mb-2"><a href="#" class="text-blue-600">Mis Planes Alimenticios</a></li>
        <li class="mb-2"><a href="#" class="text-blue-600">Publicar Contenido</a></li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>
    <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold">Entrenador Dashboard</h1>
      <div class="mt-4">
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
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rutinas" :key="r.id" class="border-t">
                <td class="px-4 py-2">{{ r.nombre }}</td>
                <td class="px-4 py-2">{{ r.nivel }}</td>
                <td class="px-4 py-2">{{ r.es_publica ? 'Sí' : 'No' }}</td>
                <td class="px-4 py-2">{{ formatDate(r.creado_en) }}</td>
              </tr>
              <tr v-if="!rutinas.length">
                <td class="px-4 py-2" colspan="4">No hay rutinas aún.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
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
    }
  },
  methods: {
    logout() {
      auth.clearSession()
      this.$router.push('/')
    },
    async fetchRutinas() {
      const session = auth.getSession()
      if (!session.user_id) return
      try {
  const res = await fetch(`/api/rutinas/${session.user_id}`, { headers: { 'X-User-Id': session.user_id } })
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
      const payload = { ...this.form, entrenador_id: session.user_id }
      try {
        const res = await fetch('/api/rutinas', {
          method: 'POST', headers: { 'Content-Type': 'application/json', 'X-User-Id': session.user_id },
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
    }
  },
  mounted() {
    this.fetchRutinas()
  }
}
</script>
