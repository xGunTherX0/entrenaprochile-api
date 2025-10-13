<template>
  <div class="min-h-screen flex bg-gray-50">
    <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Usuario</h2>
      <ul>
        <li class="mb-2"><a href="#" class="text-blue-600">Inicio</a></li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>
    <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold">Home</h1>
      <p class="mt-4">Usuario genérico.</p>
    </main>
  </div>
</template>

<script>
export default {
  name: 'Home',
  methods: {
    logout() {
      const auth = require('../utils/auth.js').default
      auth.clearSession()
      this.$router.push('/')
    }
  }
}
</script>
