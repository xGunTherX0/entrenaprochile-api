<template>
  <div class="min-h-screen flex items-center justify-center bg-black text-white p-6">
    <div class="w-full max-w-2xl">
      <div class="bg-gray-900/60 rounded-xl p-8 shadow-lg text-center">
        <h2 class="text-2xl font-bold mb-4">Registro deshabilitado</h2>
        <p class="text-gray-300 mb-4">El registro directo está deshabilitado. Por favor, inicia sesión usando Google desde la página de inicio.</p>
        <router-link to="/login" class="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-400 to-green-400 text-black font-semibold rounded-full shadow">Ir a Iniciar sesión</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'
import auth from '../utils/auth.js'

export default {
  name: 'Register',
  data() {
    return {
      role: null,
      nombre: '',
      email: '',
      password: '',
      saving: false,
      msg: ''
    }
  },
  computed: {
    roleLabel() {
      return this.role === 'entrenador' ? 'Entrenador' : 'Deportista'
    }
  },
  methods: {
    choose(r) { this.role = r },
    async submit() {
      this.saving = true
      this.msg = ''
      try {
        const res = await api.post('/api/usuarios/register', { email: this.email, nombre: this.nombre, password: this.password })
        const body = await res.json().catch(() => ({}))
        if (!res.ok) {
          this.msg = body.error || 'Error creando usuario'
          this.saving = false
          return
        }

        // Auto-login after registration
        const log = await api.post('/api/usuarios/login', { email: this.email, password: this.password }, { skipAuth: true })
        const jb = await log.json().catch(() => ({}))
        if (log.ok && jb.token) {
          auth.setSession({ user_id: jb.user_id, role: jb.role, nombre: jb.nombre, token: jb.token })
          // redirect depending on desired role / returned role
          if (this.role === 'entrenador') {
            // may not be trainer yet in backend; send to entrenador landing
            this.$router.push('/entrenador/perfil')
          } else {
            this.$router.push('/cliente/mediciones')
          }
          return
        }

        // fallback: go to login
        this.$router.push('/login')
      } catch (e) {
        this.msg = e.message || String(e)
      } finally {
        this.saving = false
      }
    }
  },
  mounted() {
    // allow preselect via query ?role=entrenador
    const r = (this.$route && this.$route.query && this.$route.query.role) ? this.$route.query.role : null
    if (r === 'entrenador' || r === 'cliente') this.role = r
  }
}
</script>

<style scoped>
.rounded-xl { border-radius: 16px; }
</style>
