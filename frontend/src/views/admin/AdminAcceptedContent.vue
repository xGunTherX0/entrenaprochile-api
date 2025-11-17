<template>
  <div>
    <h2 class="text-xl font-semibold mb-4">Contenido Aceptado por Entrenadores</h2>
    <div v-if="loading">Cargando...</div>
    <div v-else-if="error" class="text-red-600">{{ error }}</div>
    <div v-else>
      <div v-for="e in data" :key="e.entrenador_id" class="mb-6 bg-white p-4 rounded shadow-sm">
        <div class="flex justify-between items-center">
          <div>
            <div class="font-semibold">{{ e.nombre || ('entrenador ' + e.entrenador_id) }}</div>
            <div class="text-sm text-gray-500">usuario: {{ e.usuario_id }}</div>
          </div>
        </div>

        <div class="mt-3">
          <h3 class="font-semibold">Rutinas</h3>
          <div v-if="!e.rutinas || e.rutinas.length===0" class="text-sm text-gray-600">No hay rutinas.</div>
          <ul v-else class="mt-2 space-y-2">
            <li v-for="r in e.rutinas" :key="r.id" class="p-3 border rounded">
              <div class="flex justify-between">
                <div>
                  <div class="font-semibold">{{ r.nombre }}</div>
                  <div class="text-sm text-gray-600">Aceptadas: {{ r.accepted_count }} • Guardadas: {{ r.saved_count }}</div>
                </div>
                <div>
                  <router-link :to="{ name: 'ClienteRutina', params: { id: r.id } }" class="px-2 py-1 bg-blue-600 text-white rounded text-sm">Ver rutina</router-link>
                </div>
              </div>
              <div v-if="r.accepted_clients && r.accepted_clients.length" class="mt-2 text-sm">
                <div class="font-semibold">Clientes con solicitud aceptada:</div>
                <ul class="list-disc ml-5">
                  <li v-for="c in r.accepted_clients" :key="'a-'+c.cliente_id">{{ c.nombre || ('cliente '+c.cliente_id) }} (usuario: {{ c.usuario_id }})</li>
                </ul>
              </div>
              <div v-if="r.saved_users && r.saved_users.length" class="mt-2 text-sm">
                <div class="font-semibold">Clientes que la guardaron:</div>
                <ul class="list-disc ml-5">
                  <li v-for="s in r.saved_users" :key="'s-'+s.cliente_id">{{ s.nombre || ('cliente '+s.cliente_id) }} (usuario: {{ s.usuario_id }})</li>
                </ul>
              </div>
            </li>
          </ul>
        </div>

        <div class="mt-3">
          <h3 class="font-semibold">Planes</h3>
          <div v-if="!e.planes || e.planes.length===0" class="text-sm text-gray-600">No hay planes.</div>
          <ul v-else class="mt-2 space-y-2">
            <li v-for="p in e.planes" :key="p.id" class="p-3 border rounded">
              <div class="flex justify-between">
                <div>
                  <div class="font-semibold">{{ p.nombre }}</div>
                  <div class="text-sm text-gray-600">Aceptadas: {{ p.accepted_count }}</div>
                </div>
                <div>
                  <router-link :to="{ name: 'ClientePlan', params: { id: p.id } }" class="px-2 py-1 bg-blue-600 text-white rounded text-sm">Ver plan</router-link>
                </div>
              </div>
              <div v-if="p.accepted_clients && p.accepted_clients.length" class="mt-2 text-sm">
                <div class="font-semibold">Clientes con solicitud aceptada:</div>
                <ul class="list-disc ml-5">
                  <li v-for="c in p.accepted_clients" :key="'p-'+c.cliente_id">{{ c.nombre || ('cliente '+c.cliente_id) }} (usuario: {{ c.usuario_id }})</li>
                </ul>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../utils/api.js'
export default {
  name: 'AdminAcceptedContent',
  data() {
    return { data: [], loading: false, error: null }
  },
  async mounted() {
    await this.load()
  },
  methods: {
    async load() {
      this.loading = true
      this.error = null
      try {
        const res = await api.get('/api/admin/entrenadores/aceptados')
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.error = j.error || `Error cargando (${res.status})`
          return
        }
        this.data = await res.json()
      } catch (e) {
        this.error = e.message || String(e)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
