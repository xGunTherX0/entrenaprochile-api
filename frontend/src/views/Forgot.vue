<template>
  <div class="min-h-screen flex items-center justify-center bg-black text-white p-6">
    <div class="w-full max-w-md bg-gray-900/60 rounded-xl p-8 shadow-lg">
      <h2 class="text-2xl font-bold mb-4">Recuperar contraseña</h2>
      <p class="text-sm text-gray-400 mb-4">Introduce tu email y te enviaremos instrucciones para restablecer la contraseña.</p>

      <form @submit.prevent="submit">
        <div class="mb-3">
          <label class="text-sm">Email</label>
          <input v-model="email" type="email" required class="w-full mt-2 px-4 py-3 rounded-xl bg-white/5" />
        </div>
        <div class="flex items-center justify-between">
          <button :disabled="sending" class="px-4 py-2 bg-green-500 rounded">{{ sending ? 'Enviando...' : 'Enviar' }}</button>
          <router-link to="/login" class="text-sm text-gray-300">Volver al login</router-link>
        </div>
      </form>

      <div v-if="info" class="mt-4 text-sm text-gray-200 bg-white/5 p-3 rounded">{{ info }}</div>
      <div v-if="token" class="mt-4 text-sm text-yellow-200 bg-black/30 p-3 rounded">Token (solo desarrollo): {{ token }}</div>
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'
export default {
  data() { return { email: '', sending: false, info: '', token: '' } },
  methods: {
    async submit() {
      this.sending = true; this.info = ''; this.token = '';
      try {
        const res = await api.post('/api/usuarios/forgot', { email: this.email }, { skipAuth: true })
        const body = await res.json().catch(() => ({}))
        if (!res.ok) {
          this.info = body.error || 'Error enviando correo'
        } else {
          this.info = body.message || 'Si el email existe, se envió un token.'
          if (body.token) this.token = body.token
        }
      } catch (e) {
        this.info = String(e)
      } finally { this.sending = false }
    }
  }
}
</script>
