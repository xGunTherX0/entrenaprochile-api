<template>
  <div class="min-h-screen flex bg-gray-50">
    <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Cliente</h2>
      <ul>
        <li class="mb-2"><router-link to="/cliente/explorar" class="text-left w-full">Explorar Rutinas</router-link></li>
        <li class="mb-2"><router-link to="/cliente/misrutinas" class="text-left w-full">Mis Rutinas</router-link></li>
        <li class="mb-2"><router-link to="/cliente/planes" class="text-left w-full">Mis Planes Nutricionales</router-link></li>
        <li class="mb-2"><router-link to="/cliente/mediciones" class="text-left w-full">Registro de Mediciones</router-link></li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>

    <main class="flex-1 p-6">
      <router-view />
    </main>
  </div>
</template>

<script>
import auth from '../utils/auth.js'

export default {
  name: 'ClienteLayout',
  methods: {
    logout() {
      auth.clearSession()
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.trainer-list button {
  text-align: left;
  width: 100%;
}
</style>
