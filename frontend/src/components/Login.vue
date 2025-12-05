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
        </div>

        <h3 class="text-2xl font-extrabold text-white mb-2">{{ isLogin ? 'Iniciar sesión' : 'Regístrate' }}</h3>
        <p class="text-sm text-gray-300 mb-4">{{ isLogin ? 'Accede para gestionar tus rutinas y clientes' : 'Crea una cuenta para empezar a usar EntrenaProChile' }}</p>

        <div v-if="error" class="mb-4">
          <div class="px-4 py-2 text-sm text-red-100 bg-red-700/20 border border-red-700/30 rounded">
            {{ error }}
          </div>
        </div>

        <div class="space-y-4">
          <div class="bg-gray-800/60 border border-gray-700 rounded-xl p-4">
            <p class="text-sm text-gray-200 mb-3 font-semibold">Crea tu cuenta con Google</p>

            <template v-if="!isLogin">
              <label class="block text-xs text-gray-300 mb-1" for="nombre">Nombre a mostrar</label>
              <input id="nombre" v-model="nombre" type="text" maxlength="120" placeholder="Tu nombre" class="w-full px-3 py-2 rounded-lg bg-gray-900 text-white border border-gray-700 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus-visible:outline-2 focus-visible:outline-cyan-400" />

              <div class="mt-3 text-xs text-gray-300">Elige tu rol</div>
              <div class="flex gap-3 mt-2">
                <label class="flex items-center gap-2 text-sm text-gray-200">
                  <input type="radio" value="cliente" v-model="desiredRole" class="text-cyan-400" /> Deportista
                </label>
                <label class="flex items-center gap-2 text-sm text-gray-200">
                  <input type="radio" value="entrenador" v-model="desiredRole" class="text-cyan-400" /> Entrenador
                </label>
              </div>
            </template>

            <div class="flex flex-col gap-3 mt-4">
              <!-- Botón oficial de Google Identity Services -->
              <div id="g_id_signin" class="min-h-[48px] flex items-center justify-center rounded-md bg-white/3 p-1" aria-hidden="false" role="region" aria-label="Google Sign-In button container"></div>
              <div v-if="!gsiReady" class="text-xs text-yellow-300">Cargando botón de Google...</div>
              <div v-if="gsiError" class="text-xs text-red-300">{{ gsiError }}</div>
              <button v-if="gsiError" @click="loadGsiScript" class="mt-2 px-3 py-2 text-xs bg-cyan-500 text-black rounded focus-visible:outline-2 focus-visible:outline-cyan-300">Reintentar cargar</button>
            </div>
            <!-- Private access: hidden behind a small link to avoid obvious admin UI -->
            <div class="mt-3">
              <button @click.prevent="showPrivateLogin = !showPrivateLogin" class="text-xs text-gray-400 hover:text-gray-200 underline">¿Tienes un acceso privado?</button>
              <div v-if="showPrivateLogin" class="bg-gray-800/60 border border-gray-700 rounded-xl p-4 mt-3">
                <p class="text-sm text-gray-200 mb-2 font-semibold">Acceso privado</p>
                <p class="text-xs text-gray-400 mb-3">Introduce tus credenciales para acceder a la zona privada.</p>
                <label class="block text-xs text-gray-300 mb-1">Email</label>
                <input v-model="adminEmailInput" type="email" class="w-full px-3 py-2 rounded-lg bg-gray-900 text-white border border-gray-700 mb-2" placeholder="tu@correo.com" />
                <label class="block text-xs text-gray-300 mb-1">Contraseña</label>
                <input v-model="adminPasswordInput" type="password" class="w-full px-3 py-2 rounded-lg bg-gray-900 text-white border border-gray-700 mb-3" placeholder="Contraseña" />
                <div class="flex items-center justify-between">
                  <div class="text-xs text-gray-300">Acceso restringido</div>
                  <button :disabled="adminLoading || !canAttemptAdminLogin" @click="handleAdminLogin" class="px-3 py-2 bg-cyan-500 text-black rounded disabled:opacity-50">Acceder</button>
                </div>
                <div v-if="adminError" class="mt-2 text-xs text-red-300">{{ adminError }}</div>
              </div>
            </div>
            <p class="text-xs text-gray-400 mt-3">Usamos tu cuenta de Google para validar el correo. Luego creamos tu perfil con el rol elegido.</p>
          </div>
        </div>
        
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Login',
  props: {
    mode: {
      type: String,
      default: 'register' // 'login' or 'register'
    }
  },
  data() {
    return {
      email: '',
      password: '',
      loading: false,
      error: null,
      nombre: '',
      desiredRole: 'cliente',
      gsiReady: false,
      gsiError: '',
      adminEmailInput: '',
      adminPasswordInput: '',
      adminLoading: false,
      adminError: null,
      showPrivateLogin: false
    }
  },
  computed: {
    isLogin() {
      return this.mode === 'login'
    }
    ,
    adminEmailEnv() {
      return import.meta.env.VITE_ADMIN_EMAIL || 'admin@test.local'
    },
    canAttemptAdminLogin() {
      try {
        return this.adminEmailInput && this.adminEmailInput.trim().toLowerCase() === this.adminEmailEnv.trim().toLowerCase()
      } catch (e) {
        return false
      }
    }
  },
  methods: {
    loadGsiScript() {
      const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
      if (!clientId) {
        console.warn('VITE_GOOGLE_CLIENT_ID not set; Google Sign-In may not work')
        this.error = 'Falta configurar Google Client ID'
        return
      }

      // If already loaded
      if (window.google && window.google.accounts && window.google.accounts.id) {
        this.renderGsiButton()
        return
      }

      const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]')
      if (existing) {
        existing.addEventListener('load', () => this.renderGsiButton(), { once: true })
        return
      }

      const s = document.createElement('script')
      s.src = 'https://accounts.google.com/gsi/client'
      s.async = true
      s.defer = true
      s.onload = () => {
        try {
          this.renderGsiButton()
        } catch (e) {
          console.error('Google Identity init failed', e)
          this.error = 'No se pudo cargar el botón de Google'
          this.gsiError = 'No se pudo cargar el botón de Google'
        }
      }
      s.onerror = () => {
        this.error = 'No se pudo cargar Google Sign-In (revisa tu conexión)'
        this.gsiError = 'No se pudo cargar Google Sign-In (revisa tu conexión)'
      }
      document.head.appendChild(s)
      // If the script doesn't initialize the button within a short time,
      // show a helpful hint about authorized origins (common developer error).
      setTimeout(() => {
        if (!this.gsiReady && !this.gsiError && clientId) {
          // show a non-fatal hint to help debug 'origin not allowed' errors
          this.gsiError = ''
          this.error = 'Si ves "The given origin is not allowed for the given client ID", añade http://localhost:5173 a Orígenes autorizados en Google Cloud Console.'
        }
      }, 2500)
    },
    renderGsiButton() {
      const container = document.getElementById('g_id_signin')
      if (!container) return
      container.innerHTML = ''
      /* global google */
      window.google.accounts.id.initialize({
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
        callback: (resp) => {
          if (resp && resp.credential) {
            this.handleGoogleCredential(resp.credential)
          }
        },
        ux_mode: 'popup',
        auto_select: false,
        cancel_on_tap_outside: true
      })
      window.google.accounts.id.renderButton(
        container,
        { theme: 'outline', size: 'large', width: '320', shape: 'pill', text: 'continue_with' }
      )
      this.gsiReady = true
      this.gsiError = ''
      // clear previous hint if rendered
      if (this.error && this.error.includes('The given origin')) this.error = null
    },
    async handleGoogleCredential(credential) {
      // credential is the id_token from Google
      this.error = null
      this.loading = true
      try {
        const api = (await import('../utils/api.js')).default
        const body = { id_token: credential }
        // Only include these fields when we're in registration mode
        if (!this.isLogin) {
          if (!this.desiredRole) {
            this.error = 'Selecciona tu rol'
            return
          }
          body.desired_role = this.desiredRole
          if (this.nombre) body.nombre = this.nombre
        }
        const res = await api.post('/api/usuarios/google_signin', body, { skipAuth: true })
        let data = null
        try {
          data = await res.json()
        } catch (e) {
          data = { error: 'invalid json response', detail: (await res.text()).slice(0, 200) }
        }
        if (!res.ok) {
          this.error = data.error || data.detail || `Google login failed (HTTP ${res.status})`
          return
        }

        const role = data.role || 'usuario'
        const nombre = data.nombre || ''
        const token = data.token
        const auth = (await import('../utils/auth.js')).default
        auth.setSession({ user_id: data.user_id, role, nombre, token })

        // Redirect
        if (role === 'entrenador') this.$router.push('/entrenador')
        else if (role === 'cliente') this.$router.push('/cliente')
        else if (role === 'admin') this.$router.push('/admin')
        else this.$router.push('/home')

      } catch (err) {
        this.error = err.message || 'Network error'
      } finally {
        this.loading = false
      }
    },
    async handleAdminLogin() {
      this.adminError = null
      if (!this.canAttemptAdminLogin) {
        this.adminError = 'El email no coincide con el administrador configurado.'
        return
      }
      if (!this.adminPasswordInput) {
        this.adminError = 'Ingresa la contraseña.'
        return
      }
      this.adminLoading = true
      try {
        const api = (await import('../utils/api.js')).default
        const res = await api.post('/api/usuarios/login', { email: this.adminEmailInput, password: this.adminPasswordInput }, { skipAuth: true })
        let data = null
        try { data = await res.json() } catch (e) { data = { error: 'invalid json response' } }
        if (!res.ok) {
          this.adminError = data.error || `Login failed (${res.status})`
          return
        }
        const role = data.role || 'usuario'
        const nombre = data.nombre || ''
        const token = data.token
        const auth = (await import('../utils/auth.js')).default
        auth.setSession({ user_id: data.user_id, role, nombre, token })
        if (role === 'entrenador') this.$router.push('/entrenador')
        else if (role === 'cliente') this.$router.push('/cliente')
        else if (role === 'admin') this.$router.push('/admin')
        else this.$router.push('/home')
      } catch (err) {
        this.adminError = err.message || 'Network error'
      } finally {
        this.adminLoading = false
      }
    }
  },
  mounted() {
    // Debug: print the build-time client id embedded by Vite
    try {
      // eslint-disable-next-line no-console
      console.log('DEBUG: VITE_GOOGLE_CLIENT_ID =', import.meta.env.VITE_GOOGLE_CLIENT_ID)
    } catch (e) {
      // ignore
    }
    // Dynamically load Google Identity Services and render button
    this.loadGsiScript()
  }
}
</script>
