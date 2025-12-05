<template>
  <aside class="fixed left-0 top-0 h-full w-64 bg-blue-600 text-white p-6 pt-12 shadow-lg z-20">
    <h2 class="text-xl font-bold mb-6 text-white">Cliente</h2>
    <ul>
      <li class="mb-2"><router-link to="/cliente/explorar" class="block w-full py-2 rounded">Explorar Rutinas</router-link></li>
      <li class="mb-2"><router-link to="/cliente/explorar-planes" class="block w-full py-2 rounded">Explorar Planes Nutricionales</router-link></li>
      <li class="mb-2"><router-link to="/cliente/misrutinas" class="block w-full py-2 rounded">Mis Rutinas</router-link></li>
      <li class="mb-2"><router-link to="/cliente/planes" class="block w-full py-2 rounded">Mis Planes Nutricionales</router-link></li>
      <li class="mb-2"><router-link to="/cliente/mediciones" class="block w-full py-2 rounded">Registro de Mediciones</router-link></li>
      <li class="mb-2"><router-link to="/cliente/entrenadores" class="block w-full py-2 rounded">Ver Entrenadores</router-link></li>
    </ul>

    <div class="mt-6">
      <button @click="$router.push('/')" class="px-3 py-2 bg-red-500 hover:bg-red-600 text-white rounded w-full">Cerrar Sesión</button>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'AuthPanel'
}
</script>

<style scoped>
a.router-link-active {
  background-color: rgba(0,0,0,0.12);
}
</style>
