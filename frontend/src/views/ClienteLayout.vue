<template>
  <div class="min-h-screen flex bg-gray-50">
    <nav class="w-64 bg-blue-600 text-white p-6 shadow-lg">
      <h2 class="text-xl font-bold mb-6 text-white">Cliente</h2>
      <ul>
        <li class="mb-2"><router-link to="/cliente/explorar" :class="$route.path === '/cliente/explorar' ? 'bg-blue-700/60 text-white font-semibold block w-full py-2 rounded' : 'text-left block w-full py-2 rounded'">Explorar Rutinas</router-link></li>
        <li class="mb-2"><router-link to="/cliente/explorar-planes" :class="$route.path === '/cliente/explorar-planes' ? 'bg-blue-700/60 text-white font-semibold block w-full py-2 rounded' : 'text-left block w-full py-2 rounded'">Explorar Planes Nutricionales</router-link></li>
        <li class="mb-2"><router-link to="/cliente/misrutinas" :class="$route.path === '/cliente/misrutinas' ? 'bg-blue-700/60 text-white font-semibold block w-full py-2 rounded' : 'text-left block w-full py-2 rounded'">Mis Rutinas</router-link></li>
        <li class="mb-2"><router-link to="/cliente/planes" :class="$route.path === '/cliente/planes' ? 'bg-blue-700/60 text-white font-semibold block w-full py-2 rounded' : 'text-left block w-full py-2 rounded'">Mis Planes Nutricionales</router-link></li>
        <li class="mb-2"><router-link to="/cliente/mediciones" :class="$route.path === '/cliente/mediciones' ? 'bg-blue-700/60 text-white font-semibold block w-full py-2 rounded' : 'text-left block w-full py-2 rounded'">Registro de Mediciones</router-link></li>
        <li class="mb-2"><router-link to="/cliente/entrenadores" :class="$route.path === '/cliente/entrenadores' ? 'bg-blue-700/60 text-white font-semibold block w-full py-2 rounded' : 'text-left block w-full py-2 rounded'">Ver Entrenadores</router-link></li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 hover:bg-red-600 text-white rounded w-full">Cerrar Sesión</button>
      </div>
    </nav>

    <main class="flex-1 p-6">
      <router-view />
      <!-- Dev debug overlay helps show API base and token during local testing -->
      <DevDebug />
    </main>
  </div>
</template>

<script>
import auth from '../utils/auth.js'
import DevDebug from '../components/DevDebug.vue'

export default {
  name: 'ClienteLayout',
  components: { DevDebug },
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
