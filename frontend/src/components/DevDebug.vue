<template>
  <div v-if="visible" class="fixed right-2 bottom-2 z-50 bg-white border rounded shadow p-3 text-sm w-80">
    <div class="font-semibold mb-2">Dev Debug</div>
    <div class="text-xs text-gray-600 mb-2">API Base: <code>{{ base }}</code></div>
    <div class="text-xs text-gray-600">Token: <strong>{{ hasToken ? 'yes' : 'no' }}</strong></div>
    <div class="text-xs text-gray-600">User id: <strong>{{ userId || '-' }}</strong></div>
    <div class="text-xs text-gray-600">Role: <strong>{{ role || '-' }}</strong></div>
    <div v-if="lastError" class="mt-2 text-xs text-red-600">Last network error: {{ lastError }}</div>
    <div class="mt-3 text-right">
      <button @click="toggle" class="px-2 py-1 bg-gray-100 rounded">{{ visible ? 'Ocultar' : 'Mostrar' }}</button>
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'

export default {
  name: 'DevDebug',
  data() {
    return { visible: true }
  },
  computed: {
    base() { return api.BASE },
    hasToken() { return !!localStorage.getItem('auth_token') },
    userId() { return localStorage.getItem('user_id') },
    role() { return localStorage.getItem('user_role') },
    lastError() { try { return api.lastNetworkError() } catch (e) { return null } }
  },
  methods: {
    toggle() { this.visible = !this.visible }
  }
}
</script>

<style scoped>
.dev-debug { font-size: 12px }
</style>
