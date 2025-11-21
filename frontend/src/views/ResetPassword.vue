<template>
  <div class="min-h-screen flex items-center justify-center bg-black text-white p-6">
    <div class="w-full max-w-md bg-gray-900/60 rounded-xl p-8 shadow-lg">
      <h2 class="text-2xl font-bold mb-4">Restablecer contraseña</h2>
      <form @submit.prevent="submit">
        <div class="mb-3">
          <label class="text-sm">Token</label>
          <input v-model="token" class="w-full mt-2 px-4 py-3 rounded-xl bg-white/5" />
        </div>
        <div class="mb-3">
          <label class="text-sm">Nueva contraseña</label>
          <input v-model="password" type="password" class="w-full mt-2 px-4 py-3 rounded-xl bg-white/5" />
        </div>
        <div class="flex items-center justify-between">
          <button :disabled="saving" class="px-4 py-2 bg-green-500 rounded">{{ saving ? 'Guardando...' : 'Cambiar contraseña' }}</button>
          <router-link to="/login" class="text-sm text-gray-300">Volver al login</router-link>
        </div>
      </form>

      <div v-if="msg" class="mt-4 text-sm text-gray-200">{{ msg }}</div>
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'
export default {
  data() { return { token: '', password: '', saving: false, msg: '' } },
  mounted() {
    // prefill token from query param
    const t = this.$route && this.$route.query && this.$route.query.token
    if (t) this.token = t
  },
  methods: {
    async submit() {
      this.saving = true; this.msg = '';
      try {
        const res = await api.post('/api/usuarios/reset_password', { token: this.token, password: this.password }, { skipAuth: true })
        const body = await res.json().catch(() => ({}))
        if (!res.ok) {
          this.msg = body.error || 'Error cambiando contraseña'
        } else {
          this.msg = body.message || 'Contraseña actualizada'
          // redirect to login after short delay
          setTimeout(() => this.$router.push('/login'), 1200)
        }
      } catch (e) { this.msg = String(e) }
      finally { this.saving = false }
    }
  }
}
</script>
