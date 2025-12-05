<template>
  <div id="app" class="min-h-screen flex flex-col">
    <SiteHeader v-if="showHeader" />
    <main :class="['flex-1 w-full', showHeader ? 'pt-4' : 'pt-0']">
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
  components: { SiteHeader, SiteFooter },
  computed: {
    // Show header on all routes except the explicit login route
    showHeader() {
      return !(this.$route && (this.$route.path === '/login' || this.$route.name === 'Login'))
    }
  }
}

</script>

