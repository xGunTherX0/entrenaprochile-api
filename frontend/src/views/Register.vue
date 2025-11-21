<template>
  <div class="min-h-screen flex items-center justify-center bg-black text-white p-6">
    <div class="w-full max-w-2xl">
      <div v-if="!role" class="bg-gray-900/60 rounded-xl p-8 shadow-lg text-center">
        <h2 class="text-2xl font-bold mb-4">¿Eres Entrenador o Deportista?</h2>
        <div class="flex items-center justify-center space-x-6 mt-6">
          <button @click="choose('cliente')" class="px-6 py-3 bg-white text-black rounded-full">Deportista</button>
          <button @click="choose('entrenador')" class="px-6 py-3 border border-white/20 rounded-full">Entrenador</button>
        </div>
      </div>

      <div v-else class="bg-gray-900/60 rounded-xl p-8 shadow-lg">
        <h2 class="text-2xl font-bold mb-4">Crear cuenta — {{ roleLabel }}</h2>
        <form @submit.prevent="submit">
          <div class="mb-3">
            <label class="block text-sm mb-1">Nombre</label>
            <input v-model="nombre" class="w-full px-3 py-2 rounded bg-black/20" required />
          </div>
          <div class="mb-3">
            <label class="block text-sm mb-1">Email</label>
            <input v-model="email" type="email" class="w-full px-3 py-2 rounded bg-black/20" required />
          </div>
          <div class="mb-3">
            <label class="block text-sm mb-1">Contraseña</label>
            <input v-model="password" type="password" class="w-full px-3 py-2 rounded bg-black/20" required minlength="6" />
          </div>
          <div class="flex items-center justify-between">
            <div>
              <button type="button" @click="role=null" class="px-4 py-2 border rounded mr-2">Volver</button>
              <button type="submit" :disabled="saving" class="px-4 py-2 bg-green-500 rounded">{{ saving ? 'Creando...' : 'Crear cuenta' }}</button>
            </div>
            <div v-if="msg" class="text-sm text-green-300">{{ msg }}</div>
          </div>
        </form>
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
