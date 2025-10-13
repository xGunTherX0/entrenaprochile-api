<template>
  <div class="min-h-screen flex bg-gray-50">
    <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Cliente</h2>
      <ul>
        <li class="mb-2"><a href="#" class="text-blue-600">Explorar Rutinas</a></li>
        <li class="mb-2"><a href="#" class="text-blue-600">Mis Planes Nutricionales</a></li>
        <li class="mb-2"><a href="#" class="text-blue-600">Registro de Mediciones</a></li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>
    <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold">Cliente Dashboard</h1>
      <p class="mt-4">Registro de Mediciones</p>

      <div class="mt-6 max-w-md bg-white p-4 rounded shadow">
        <form @submit.prevent="submitMedicion">
          <div class="mb-3">
            <label class="block text-sm">Peso (kg)</label>
            <input v-model.number="peso" type="number" step="0.1" class="w-full px-3 py-2 border rounded" />
          </div>
          <div class="mb-3">
            <label class="block text-sm">Altura (cm)</label>
            <input v-model.number="altura" type="number" step="0.1" class="w-full px-3 py-2 border rounded" />
          </div>
          <div class="mb-3">
            <label class="block text-sm">Circunferencia de Cintura (cm)</label>
            <input v-model.number="cintura" type="number" step="0.1" class="w-full px-3 py-2 border rounded" />
          </div>
          <div class="flex items-center justify-between">
            <button :disabled="saving" class="px-4 py-2 bg-green-600 text-white rounded">{{ saving ? 'Guardando...' : 'Guardar medición' }}</button>
            <div v-if="msg" class="text-sm text-green-600">{{ msg }}</div>
          </div>
        </form>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'ClienteDashboard',
  methods: {
</script>

<script>
export default {
  name: 'ClienteDashboard',
  data() {
    return {
      peso: null,
      altura: null,
      cintura: null,
      saving: false,
      msg: ''
    }
  },
  methods: {
    async submitMedicion() {
      this.saving = true
      this.msg = ''
      try {
        const base = import.meta.env.VITE_API_BASE || 'http://localhost:5000'
        const user_id = localStorage.getItem('user_id')
        const res = await fetch(`${base}/api/mediciones`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cliente_id: user_id, peso: this.peso, altura: this.altura, cintura: this.cintura })
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Error al guardar')
        this.msg = 'Medición guardada con id ' + data.id
        this.peso = this.altura = this.cintura = null
      } catch (err) {
        this.msg = err.message
      } finally {
        this.saving = false
      }
    }
  }
}
    logout() {
      const auth = require('../utils/auth.js').default
      auth.clearSession()
      this.$router.push('/')
    }
  }
}
</script>
