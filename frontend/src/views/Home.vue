<template>
  <div class="min-h-screen bg-black text-white">
    <!-- Top navigation -->
    <header class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 bg-gradient-to-r from-blue-600 to-cyan-400 rounded flex items-center justify-center">
          <!-- Inline SVG logo to avoid missing file import -->
          <svg class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M12 2L15 8H9L12 2Z" fill="white"/>
            <path d="M3 22L12 13L21 22H3Z" fill="white"/>
            <path d="M7 11H17V13H7V11Z" fill="white"/>
          </svg>
        </div>
        <span class="font-extrabold text-xl">EntrenaPro</span>
      </div>
      <nav class="space-x-6">
        <router-link to="/login" class="text-sm text-gray-200 hover:text-white">Inicia sesión</router-link>
        <a href="#" class="text-sm text-gray-200 hover:text-white">Regístrate</a>
      </nav>
    </header>

    <!-- Hero -->
    <section class="relative">
      <div class="h-[68vh] md:h-[78vh] bg-cover bg-center" :style="heroStyle">
        <div class="absolute inset-0 bg-black/60"></div>
        <div class="relative max-w-6xl mx-auto px-6 py-20">
          <div class="max-w-2xl text-white">
            <h1 class="text-4xl md:text-6xl font-extrabold leading-tight mb-4">Bienvenido a EntrenaPro</h1>
            <p class="text-lg md:text-xl text-gray-200/90 mb-8">La mejor plataforma para entrenadores y deportistas. Conecta, crea rutinas y monetiza tu trabajo.</p>
            <div class="flex items-center space-x-4">
              <router-link to="/login" class="px-6 py-3 bg-green-500 rounded text-white font-medium shadow hover:bg-green-600">Iniciar sesión</router-link>
              <router-link to="/cliente/explorar" class="px-6 py-3 border border-white/20 rounded text-white/90 hover:bg-white/5">Explorar rutinas</router-link>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features / content placeholder -->
    <main class="max-w-6xl mx-auto px-6 py-16">
      <h2 class="text-3xl font-bold text-white mb-6">Beneficios Clave para Entrenadores</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-gray-200">
        <div class="bg-gray-900/40 p-6 rounded-md">Crea rutinas profesionales y véndelas</div>
        <div class="bg-gray-900/40 p-6 rounded-md">Administra tus clientes y mediciones</div>
        <div class="bg-gray-900/40 p-6 rounded-md">Recibe solicitudes y gestiona aprobaciones</div>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  name: 'Home',
  computed: {
    heroStyle() {
      // Use the user-provided image URL for the hero background.
      // Note: Hotlinking third-party images (Shutterstock, etc.) may be blocked
      // or require licensing. If this image doesn't load, download it and
      // put it in `frontend/public/hero.jpg` and change the URL to '/hero.jpg'.
      const url = 'https://www.shutterstock.com/image-photo/home-workout-man-doing-ab-260nw-1132404866.jpg'
      return `background-image: url(${url}); background-size: cover; background-position: center;`;
    }
  }
}
</script>
