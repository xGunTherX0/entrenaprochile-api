<template>
  <footer class="w-full py-8 mt-12 border-t border-white/6">
    <div class="container-max flex flex-col md:flex-row items-center justify-between gap-4">
      <div class="text-sm text-gray-300">2025 EntrenaProChile - Derechos Reservados por CFMC</div>
      <div class="flex items-center gap-3">
        <a href="#" class="text-gray-300 hover:text-white text-sm">Términos</a>
        <a href="#" class="text-gray-300 hover:text-white text-sm">Privacidad</a>
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
