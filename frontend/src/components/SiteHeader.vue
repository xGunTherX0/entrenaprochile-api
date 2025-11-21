<template>
  <header class="absolute inset-x-0 top-0 z-50">
    <div class="container-max flex items-center justify-between py-4">
      <div class="flex items-center gap-3">
        <div class="w-11 h-11 rounded-lg bg-gradient-to-r from-cyan-400 to-green-400 flex items-center justify-center shadow-md">
          <svg class="w-6 h-6 text-black" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L15 8H9L12 2Z" fill="black"/><path d="M3 22L12 13L21 22H3Z" fill="black"/><path d="M7 11H17V13H7V11Z" fill="black"/></svg>
        </div>
        <div>
          <router-link to="/" class="font-extrabold text-lg text-white">EntrenaProChile</router-link>
          <div class="text-xs text-gray-300">Entrenadores · Clientes · Planes</div>
        </div>
      </div>

      <nav class="flex items-center gap-4">
        <router-link to="/explorar" class="text-sm text-white/90 hover:text-white">Explorar</router-link>
        <router-link to="/login" class="px-4 py-2 bg-white/6 hover:bg-white/10 rounded-full text-sm">Inicia sesión</router-link>
      </nav>
    </div>
  </header>
</template>

<script>
export default {
  name: 'SiteHeader'
}
</script>
