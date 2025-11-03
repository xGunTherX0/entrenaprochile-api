<template>
  <div class="flex items-center justify-center min-h-screen bg-gray-100">
    <div class="px-8 py-6 mt-4 text-left bg-white shadow-lg">
      <h3 class="text-2xl font-bold text-center">Login</h3>
      <!-- Error visible para el usuario -->
      <div v-if="error" class="mt-4 text-center">
        <div class="inline-block px-4 py-2 text-sm text-red-700 bg-red-100 border border-red-200 rounded">
          {{ error }}
        </div>
      </div>
      <form @submit.prevent="onSubmit">
        <div class="mt-4">
          <div>
            <label class="block" for="email">Email</label>
            <input v-model="email" type="text" placeholder="Email"
              class="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600">
          </div>
          <div class="mt-4">
            <label class="block">Password</label>
            <input v-model="password" type="password" placeholder="Password"
              class="w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-600">
          </div>
          <div class="flex items-baseline justify-between">
            <button :disabled="loading"
              class="px-6 py-2 mt-4 text-white bg-[#1ED66C] rounded-lg hover:bg-green-500 disabled:opacity-50">
              {{ loading ? 'Logging...' : 'Login' }}
            </button>
            <a href="#" class="text-sm text-blue-600 hover:underline">Forgot password?</a>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Login',
  data() {
    return {
      email: '',
      password: '',
      loading: false,
      error: null
    }
  },
  methods: {
    async onSubmit() {
      this.error = null
      this.loading = true
      try {
  // Ajusta la baseURL según entorno. En producción Netlify sirve frontend y backend separado.
  // Si VITE_API_BASE no está definida en el entorno de Netlify, usar la URL pública del backend en Render.
  const base = import.meta.env.VITE_API_BASE || 'https://entrenaprochile-api.onrender.com'
        const res = await fetch(`${base}/api/usuarios/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: this.email, password: this.password })
        })

        const data = await res.json()
        if (!res.ok) {
          this.error = data.error || 'Login failed'
          this.loading = false
          return
        }

  // data should include { message, user_id, role, nombre, token }
  const role = data.role || 'usuario'
  const nombre = data.nombre || ''
  const token = data.token

  // Guarda en sesión usando helper (incluye token JWT)
  const auth = (await import('../utils/auth.js')).default
  auth.setSession({ user_id: data.user_id, role, nombre, token })

        // Redirige según rol
        if (role === 'entrenador') {
          this.$router.push('/entrenador')
        } else if (role === 'cliente') {
          this.$router.push('/cliente')
        } else if (role === 'admin') {
          this.$router.push('/admin')
        } else {
          this.$router.push('/home')
        }

      } catch (err) {
        this.error = err.message || 'Network error'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
