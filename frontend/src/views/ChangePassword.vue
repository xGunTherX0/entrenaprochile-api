<template>
  <div class="max-w-md mx-auto mt-12 p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
    <h2 class="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-100">Cambiar contraseña</h2>
    <p class="text-sm text-gray-600 dark:text-gray-300 mb-4">Para un flujo rápido deja el campo "Contraseña actual" vacío y se intentará el modo rápido (solo si el servidor lo permite).</p>

    <div v-if="message" :class="messageClass" class="p-2 mb-4 rounded">{{ message }}</div>

    <form @submit.prevent="submit">
      <label class="block mb-2 text-sm text-gray-700 dark:text-gray-200">Contraseña actual (opcional)</label>
      <input v-model="oldPassword" type="password" class="w-full p-2 mb-3 border rounded bg-gray-50 dark:bg-gray-700" />

      <label class="block mb-2 text-sm text-gray-700 dark:text-gray-200">Nueva contraseña</label>
      <input v-model="newPassword" type="password" class="w-full p-2 mb-3 border rounded bg-gray-50 dark:bg-gray-700" />

      <label class="block mb-2 text-sm text-gray-700 dark:text-gray-200">Confirmar nueva contraseña</label>
      <input v-model="confirmPassword" type="password" class="w-full p-2 mb-4 border rounded bg-gray-50 dark:bg-gray-700" />

      <button type="submit" class="w-full py-2 px-4 bg-gradient-to-r from-green-500 to-purple-600 text-white rounded hover:opacity-95">Cambiar contraseña</button>
    </form>
  </div>
</template>

<script>
import auth from '../utils/auth.js'
export default {
  name: 'ChangePassword',
  data() {
    return {
      oldPassword: '',
      newPassword: '',
      confirmPassword: '',
      message: null,
      messageClass: ''
    }
  },
  methods: {
    async submit() {
      this.message = null
      if (!this.newPassword) {
        this.message = 'Ingresa la nueva contraseña.'
        this.messageClass = 'bg-red-100 text-red-700'
        return
      }
      if (this.newPassword !== this.confirmPassword) {
        this.message = 'Las contraseñas no coinciden.'
        this.messageClass = 'bg-red-100 text-red-700'
        return
      }

      const token = auth.getAuthToken()
      if (!token) {
        this.message = 'Debes iniciar sesión para cambiar tu contraseña.'
        this.messageClass = 'bg-red-100 text-red-700'
        return
      }

      // Decide endpoint: if oldPassword provided use change_password, else try set_password
      const useOld = !!this.oldPassword
      const url = useOld ? '/api/usuarios/change_password' : '/api/usuarios/set_password'
      const body = useOld ? { old_password: this.oldPassword, new_password: this.newPassword } : { new_password: this.newPassword }

      try {
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
          body: JSON.stringify(body)
        })
        const data = await res.json()
        if (!res.ok) {
          this.message = data.error || data.message || JSON.stringify(data)
          this.messageClass = 'bg-red-100 text-red-700'
          // If quick set not allowed and we tried set_password, suggest using old password
          if (res.status === 403 && !useOld) {
            this.message += ' — Intenta ingresar tu contraseña actual y usar el modo tradicional.'
          }
          return
        }

        this.message = data.message || 'Contraseña cambiada correctamente.'
        this.messageClass = 'bg-green-100 text-green-700'
        // clear inputs
        this.oldPassword = ''
        this.newPassword = ''
        this.confirmPassword = ''
      } catch (err) {
        this.message = 'Error de red: ' + String(err)
        this.messageClass = 'bg-red-100 text-red-700'
      }
    }
  }
}
</script>

<style scoped>
/* small adjustments to fit existing theme */
</style>
