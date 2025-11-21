<template>
  <div class="min-h-screen flex items-center justify-center p-6 bg-gray-900 text-white">
    <div class="w-full max-w-md surface-card overflow-hidden">
      <div class="px-8 py-8">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 bg-gradient-to-r from-blue-600 to-cyan-400 rounded flex items-center justify-center">
              <svg class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M12 2L15 8H9L12 2Z" fill="white"/><path d="M3 22L12 13L21 22H3Z" fill="white"/><path d="M7 11H17V13H7V11Z" fill="white"/></svg>
            </div>
            <div>
              <div class="text-lg font-bold">EntrenaProChile</div>
              <div class="text-xs text-gray-400">Inicia sesión en tu cuenta</div>
            </div>
          </div>
          <router-link to="/register" class="text-sm text-gray-300 hover:text-white">Regístrate</router-link>
        </div>

        <h3 class="text-2xl font-extrabold text-white mb-2">Iniciar sesión</h3>
        <p class="text-sm text-gray-300 mb-4">Accede para gestionar tus rutinas y clientes</p>

        <div v-if="error" class="mb-4">
          <div class="px-4 py-2 text-sm text-red-100 bg-red-700/20 border border-red-700/30 rounded">
            {{ error }}
          </div>
        </div>

        <form @submit.prevent="onSubmit">
          <div class="space-y-4">
            <div>
              <label class="text-sm text-gray-300">Email</label>
              <input v-model="email" type="text" placeholder="Correo electrónico"
                class="w-full mt-2 px-4 py-3 rounded-xl bg-white/90 text-gray-900 placeholder-gray-500 border border-white/5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-400" />
            </div>

            <div>
              <label class="text-sm text-gray-300">Contraseña</label>
              <input v-model="password" type="password" placeholder="Contraseña"
                class="w-full mt-2 px-4 py-3 rounded-xl bg-white/90 text-gray-900 placeholder-gray-500 border border-white/5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500" />
            </div>

            <div class="flex items-center justify-between">
              <button :disabled="loading" class="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-400 to-green-400 text-black font-semibold rounded-full shadow disabled:opacity-60 focus-ring">
                <svg v-if="loading" class="w-4 h-4 animate-spin" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" stroke="rgba(0,0,0,0.2)" stroke-width="4" fill="none" /></svg>
                {{ loading ? 'Conectando...' : 'Iniciar sesión' }}
              </button>
              <router-link to="/forgot" class="text-sm text-gray-300 hover:text-white">¿Olvidaste tu contraseña?</router-link>
            </div>
          </div>
        </form>
      </div>
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
