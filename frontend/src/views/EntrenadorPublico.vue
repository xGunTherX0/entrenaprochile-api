<template>
  <div class="p-4 text-gray-800">
    <h1 class="text-2xl font-bold mb-3 text-indigo-800">Perfil de Entrenador</h1>
    <div v-if="loading" class="text-gray-600">Cargando...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>

    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- Left column: profile info (visible to all) -->
      <div class="col-span-1 bg-white p-4 rounded shadow-sm text-gray-800">
        <h2 class="text-lg font-semibold text-indigo-800">{{ perfil.nombre }}</h2>
        <div class="text-sm text-gray-700">{{ perfil.speciality || 'Sin especialidad' }}</div>
        <div class="mt-3 text-sm text-gray-700">{{ perfil.bio }}</div>
        <div class="mt-3">
          <a v-if="perfil.email" :href="`mailto:${perfil.email}`" class="text-blue-600">Contactar por email</a>
          <div class="mt-2">
            <a v-if="perfil.instagram_url" :href="perfil.instagram_url" target="_blank" rel="noopener noreferrer" class="inline-flex items-center text-pink-600 hover:underline">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 mr-2" aria-hidden="true">
                <path d="M7 2C4.243 2 2 4.243 2 7v10c0 2.757 2.243 5 5 5h10c2.757 0 5-2.243 5-5V7c0-2.757-2.243-5-5-5H7zm0 2h10c1.654 0 3 1.346 3 3v10c0 1.654-1.346 3-3 3H7c-1.654 0-3-1.346-3-3V7c0-1.654 1.346-3 3-3zm5 3.5a4.5 4.5 0 100 9 4.5 4.5 0 000-9zm0 2a2.5 2.5 0 110 5 2.5 2.5 0 010-5zm4.75-3.25a1 1 0 100 2 1 1 0 000-2z" />
              </svg>
              <span>Instagram</span>
            </a>
            <a v-if="perfil.youtube_url" :href="perfil.youtube_url" target="_blank" rel="noopener noreferrer" class="inline-flex items-center text-red-600 hover:underline ml-3">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 mr-2" aria-hidden="true">
                <path d="M23.5 6.2s-.2-1.7-.8-2.5c-.8-1.1-1.7-1.1-2.1-1.2C16.9 2 12 2 12 2s-4.9 0-8.6.5c-.4.1-1.3.1-2.1 1.2C.9 4.5.7 6.2.7 6.2S.5 8 .5 9.8v4.4c0 1.8.2 3.6.2 3.6s.2 1.7.8 2.5c.8 1.1 1.8 1.1 2.3 1.2 1.7.2 7.1.5 9.7.5 2.6 0 7.9-.3 9.7-.5.5-.1 1.5-.1 2.3-1.2.6-.8.8-2.5.8-2.5s.2-1.8.2-3.6V9.8c0-1.8-.2-3.6-.2-3.6zM9.8 15.1V8.9l6.2 3.1-6.2 3.1z" />
              </svg>
              <span>YouTube</span>
            </a>
          </div>
        </div>

        <div v-if="perfil.telefono" class="mt-2 text-sm">Tel: {{ perfil.telefono }}</div>

        <!-- Instagram QR: muestra un código QR del URL de Instagram en la tarjeta del perfil -->
        <div v-if="perfil.instagram_url" class="mt-4">
          <img :src="`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(perfil.instagram_url)}`" alt="QR Instagram" class="w-40 h-40 rounded border" />
        </div>
      </div>

      <!-- Right column: only show lists for non-client users -->
      <div class="col-span-2">
        <!-- If visitor is a cliente, show simplified lists (name + first line of description) without buttons/QR -->
        <section v-if="isCliente" class="bg-white p-4 rounded shadow-sm mb-4">
          <h3 class="font-semibold mb-2 text-indigo-800">Rutinas públicas</h3>
          <div v-if="!perfil.rutinas || !perfil.rutinas.length" class="text-sm text-gray-700">No hay rutinas públicas.</div>
          <ul v-else class="space-y-2">
            <li v-for="r in perfil.rutinas" :key="r.id" class="border rounded p-2">
              <div class="font-semibold text-indigo-800">{{ r.nombre }}</div>
              <div class="text-sm text-gray-700">{{ (r.descripcion || '').split('\n')[0] }}</div>
            </li>
          </ul>
        </section>

        <section v-if="isCliente" class="bg-white p-4 rounded shadow-sm">
          <h3 class="font-semibold mb-2">Planes públicos</h3>
          <div v-if="!perfil.planes || !perfil.planes.length" class="text-sm text-gray-600">No hay planes públicos.</div>
          <ul v-else class="space-y-2">
            <li v-for="p in perfil.planes" :key="p.id" class="border rounded p-2">
              <div class="font-semibold">{{ p.nombre }}</div>
              <div class="text-sm text-gray-600">{{ (p.descripcion || '').split('\n')[0] }}</div>
            </li>
          </ul>
        </section>

        <!-- Non-client users see the full interactive lists -->
        <div v-if="!isCliente">
          <section class="bg-white p-4 rounded shadow-sm mb-4">
            <h3 class="font-semibold mb-2 text-indigo-800">Rutinas públicas</h3>
              <div v-if="!perfil.rutinas || !perfil.rutinas.length" class="text-sm text-gray-700">No hay rutinas públicas.</div>
            <ul v-else class="space-y-2">
              <li v-for="r in perfil.rutinas" :key="r.id" class="border rounded p-2 flex justify-between items-center">
                  <div>
                  <div class="font-semibold text-indigo-800">{{ r.nombre }}</div>
                  <div class="text-sm text-gray-700">{{ r.nivel }}</div>
                </div>
                <div class="flex items-center space-x-2">
                  <router-link :to="{ name: 'ClienteRutina', params: { id: r.id } }" class="px-2 py-1 bg-blue-600 text-white rounded">Ver</router-link>
                  <a v-if="r.link_url" :href="r.link_url" target="_blank" rel="noopener noreferrer" class="px-2 py-1 bg-green-600 text-white rounded text-sm">Abrir link</a>
                  <img v-if="r.link_url" :src="`https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=${encodeURIComponent(r.link_url)}`" alt="QR" class="w-16 h-16 rounded border" />
                </div>
              </li>
            </ul>
          </section>

          <section class="bg-white p-4 rounded shadow-sm">
            <h3 class="font-semibold mb-2">Planes públicos</h3>
            <div v-if="!perfil.planes || !perfil.planes.length" class="text-sm text-gray-600">No hay planes públicos.</div>
            <ul v-else class="space-y-2">
              <li v-for="p in perfil.planes" :key="p.id" class="border rounded p-2 flex justify-between items-center">
                <div>
                  <div class="font-semibold">{{ p.nombre }}</div>
                  <div class="text-sm text-gray-600">{{ p.descripcion }}</div>
                </div>
                <router-link :to="{ name: 'ClientePlan', params: { id: p.id } }" class="px-2 py-1 bg-blue-600 text-white rounded">Ver</router-link>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../utils/api.js'
import auth from '../utils/auth.js'
export default {
  name: 'EntrenadorPublico',
  props: ['id'],
  data() {
    return {
      perfil: null,
      loading: false,
      error: null
    }
  },
  computed: {
    isCliente() {
      return auth.getRole && auth.getRole() === 'cliente'
    }
  },
  async created() {
    await this.load()
  },
  watch: {
    id: 'load'
  },
  methods: {
    async load() {
      this.loading = true
      this.error = null
      try {
  // Public profile: request without Authorization header to avoid preflight
  const res = await api.get(`/api/public/entrenadores/${this.id}`, { skipAuth: true })
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || `Error fetching profile (${res.status})`
          return
        }
        this.perfil = await res.json()
      } catch (e) {
        this.error = e.message || String(e)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
