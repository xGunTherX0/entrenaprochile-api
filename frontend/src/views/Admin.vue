<template>
  <div class="min-h-screen flex bg-gray-50">
    <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Admin</h2>
      <ul>
        <li class="mb-2"><a href="#" class="text-blue-600">Gestionar Usuarios</a></li>
        <li class="mb-2"><a href="#" class="text-blue-600">Aprobar Contenido</a></li>
        <li class="mb-2"><a href="#" class="text-blue-600">Métricas</a></li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>
    <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold">Admin Dashboard</h1>
      <p class="mt-4">Panel básico para administradores.</p>
    </main>
  </div>
</template>

<script>
export default {
  name: 'Admin',
  methods: {
    logout() {
      // Limpia la sesión mínima
      localStorage.removeItem('user_role')
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_nombre')
      this.$router.push('/')
    }
  }
}
</script>

<script>
export default {
  name: 'Admin'
}
</script>
