<template>
  <div id="app" class="min-h-screen flex flex-col">
    <SiteHeader v-if="$route && ($route.path === '/login' || $route.name === 'Login')" />
    <main class="flex-1 w-full pt-20">
      <router-view />
    </main>
    <SiteFooter />
  </div>
</template>

<script>
import SiteHeader from './components/SiteHeader.vue'
import SiteFooter from './components/SiteFooter.vue'

export default {
  name: 'App',
  components: { SiteHeader, SiteFooter }
}
</script>
