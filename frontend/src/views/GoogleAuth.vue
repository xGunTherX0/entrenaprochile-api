<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-900 text-white p-6">
    <div class="w-full max-w-md bg-white/5 rounded-xl p-8 shadow-lg">
      <div class="flex items-center gap-4 mb-6">
        <div class="w-12 h-12 rounded-lg bg-gradient-to-r from-cyan-400 to-green-400 flex items-center justify-center shadow-md">
          <svg class="w-6 h-6 text-black" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M12 2L15 8H9L12 2Z" fill="black"/><path d="M3 22L12 13L21 22H3Z" fill="black"/><path d="M7 11H17V13H7V11Z" fill="black"/></svg>
        </div>
        <div>
          <h2 class="text-xl font-extrabold">Iniciar sesión con Google</h2>
          <p class="text-sm text-gray-300">Usa tu cuenta de Google para iniciar sesión</p>
        </div>
      </div>

      <div class="space-y-4">
        <div class="bg-gray-800/60 border border-gray-700 rounded-xl p-6">
          <div id="g_id_signin" class="min-h-[48px] flex items-center justify-center rounded-md bg-white/3 p-1" aria-hidden="false" role="region" aria-label="Google Sign-In button container"></div>
          <div v-if="!gsiReady" class="mt-2 text-sm text-yellow-300">Cargando botón de Google...</div>
          <div v-if="gsiError" class="mt-2 text-sm text-red-300">{{ gsiError }}</div>
          <div v-if="gsiError" class="mt-2"><button @click="loadGsiScript" class="px-3 py-2 bg-cyan-500 text-black rounded">Reintentar</button></div>
        </div>

        <div class="text-sm text-gray-400">Si ya tienes cuenta, puedes continuar con Google y se mapeará al rol registrado en el sistema.</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GoogleAuth',
  data() {
    return {
      gsiReady: false,
      gsiError: ''
    }
  },
  methods: {
    loadGsiScript() {
      const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
      if (!clientId) {
        this.gsiError = 'Falta configurar Google Client ID'
        return
      }

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
          this.gsiError = 'No se pudo inicializar Google Identity'
        }
      }
      s.onerror = () => {
        this.gsiError = 'No se pudo cargar Google Sign-In (revisa tu conexión)'
      }
      document.head.appendChild(s)
      setTimeout(() => {
        if (!this.gsiReady && !this.gsiError && clientId) {
          this.gsiError = 'Si ves "The given origin is not allowed for the given client ID", añade http://localhost:5173 a Orígenes autorizados en Google Cloud Console.'
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
    }
  },
  methods: {
    async handleGoogleCredential(credential) {
      this.gsiError = ''
      try {
        const res = await fetch('/api/usuarios/google_signin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id_token: credential })
        })
        const j = await res.json()
        if (!res.ok) {
          this.gsiError = j && j.error ? (j.detail || j.error) : 'Error en autenticación con Google'
          return
        }
        // Save session like other flows
        try {
          const { default: auth } = await import('/src/utils/auth.js')
          auth.setSession({ user_id: j.user_id, role: j.role, nombre: j.nombre, token: j.token })
        } catch (e) {
          console.warn('Could not set session via auth helper', e)
          localStorage.setItem('user_id', j.user_id)
          localStorage.setItem('user_role', j.role)
          localStorage.setItem('user_nombre', j.nombre)
          localStorage.setItem('auth_token', j.token)
        }

        // Redirect according to role
        if (j.role === 'entrenador') {
          this.$router.push('/entrenador')
        } else if (j.role === 'cliente') {
          this.$router.push('/cliente')
        } else if (j.role === 'admin') {
          this.$router.push('/admin')
        } else {
          this.$router.push('/cliente')
        }
      } catch (e) {
        console.error('google signin failed', e)
        this.gsiError = 'Error comunicándose con el servidor. Revisa la consola.'
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
    this.loadGsiScript()
  }
}
</script>
