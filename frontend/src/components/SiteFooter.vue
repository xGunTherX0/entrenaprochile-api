<template>
  <footer class="w-full py-6 mt-12 border-t border-gray-800 bg-gray-900 text-gray-100">
    <div class="container-max flex flex-col md:flex-row items-center justify-between gap-4">
      <div class="text-sm text-gray-200 font-medium">2025 EntrenaProChile - Derechos Reservados por CFMC</div>
      <div class="flex items-center gap-4">
        <a href="#" class="text-gray-200 hover:text-white text-sm">Términos</a>
        <a href="#" class="text-gray-200 hover:text-white text-sm">Privacidad</a>
      </div>
    </div>
  </footer>
</template>

<script>
export default {
  name: 'SiteFooter',
  data() { return { year: new Date().getFullYear() } }
}
</script>
