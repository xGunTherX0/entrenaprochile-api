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
        // Use centralized API helper
        const api = (await import('../utils/api.js')).default
        const res = await api.post('/api/usuarios/login', { email: this.email, password: this.password }, { skipAuth: true })
        const data = await res.json()
        if (!res.ok) {
          this.error = data.error || 'Login failed'
          this.loading = false
          return
        }

        const role = data.role || 'usuario'
        const nombre = data.nombre || ''
        const token = data.token

        // Guarda en sesión usando helper (incluye token JWT)
        const auth = (await import('../utils/auth.js')).default
        auth.setSession({ user_id: data.user_id, role, nombre, token })

        // Sincronizar rutinas guardadas localmente con el servidor
        try {
          const api = (await import('../utils/api.js')).default
          const toast = (await import('../utils/toast.js')).default
          const saved = JSON.parse(localStorage.getItem('saved_rutinas') || '[]')
          if (Array.isArray(saved) && saved.length > 0) {
            // Intentar sincronizar en paralelo, pero no bloquear demasiado la UI
            // Create solicitudes for saved rutinas so the trainer must approve them
            const promises = saved.map(id => api.post(`/api/rutinas/${id}/solicitar`, {}))
            const results = await Promise.allSettled(promises)
            // Contar éxitos
            let success = 0
            const failedIds = []
            for (let i = 0; i < results.length; i++) {
              const r = results[i]
              const id = saved[i]
              if (r.status === 'fulfilled') {
                try {
                  // check response ok
                  const res = r.value
                  if (res && res.ok) {
                    success++
                  } else {
                    failedIds.push(id)
                  }
                } catch (e) {
                  failedIds.push(id)
                }
              } else {
                failedIds.push(id)
              }
            }
            if (success > 0) {
              toast.show(`${success} solicitudes de rutina creadas (esperando aprobación)`, 3000)
            }
            // Guardar el resto (fallidos) en localStorage para reintentos futuros
            try {
              localStorage.setItem('saved_rutinas', JSON.stringify(failedIds))
            } catch (e) {}
          }
        } catch (e) {
          // Si falla el proceso de sincronización, no bloqueamos el login
          try { (await import('../utils/toast.js')).default.show('No se pudo sincronizar rutinas ahora, se intentará luego', 2500) } catch (_) {}
        }

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
