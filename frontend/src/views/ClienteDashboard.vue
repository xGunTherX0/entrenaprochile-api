<template>
  <div class="min-h-screen flex bg-gray-50">
    <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Cliente</h2>
      <ul>
  <li class="mb-2"><button @click="select('explorar')" :class="{'text-blue-600 font-semibold': activePanel==='explorar'}" class="text-left w-full">Explorar Rutinas</button></li>
  <li class="mb-2"><button @click="select('misrutinas')" :class="{'text-blue-600 font-semibold': activePanel==='misrutinas'}" class="text-left w-full">Mis Rutinas</button></li>
  <li class="mb-2"><button @click="select('planes')" :class="{'text-blue-600 font-semibold': activePanel==='planes'}" class="text-left w-full">Mis Planes Nutricionales</button></li>
        <li class="mb-2"><button @click="select('mediciones')" :class="{'text-blue-600 font-semibold': activePanel==='mediciones'}" class="text-left w-full">Registro de Mediciones</button></li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>
    <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold">Cliente Dashboard</h1>

      <section v-if="activePanel === 'mediciones'">
        <p class="mt-4">Registro de Mediciones</p>

        <div class="mt-6 max-w-md bg-white p-4 rounded shadow">
        <form @submit.prevent="submitMedicion">
          <div class="mb-3">
            <label class="block text-sm">Peso (kg)</label>
            <input v-model.number="peso" type="number" step="0.1" class="w-full px-3 py-2 border rounded" />
          </div>
          <div class="mb-3">
            <label class="block text-sm">Altura (cm)</label>
            <input v-model.number="altura" type="number" step="0.1" class="w-full px-3 py-2 border rounded" />
          </div>
          <div class="mb-3">
            <label class="block text-sm">Circunferencia de Cintura (cm)</label>
            <input v-model.number="cintura" type="number" step="0.1" class="w-full px-3 py-2 border rounded" />
          </div>
          <div class="flex items-center justify-between">
            <button :disabled="saving" class="px-4 py-2 bg-green-600 text-white rounded">{{ saving ? 'Guardando...' : 'Guardar medición' }}</button>
            <div v-if="msg" class="text-sm text-green-600">{{ msg }}</div>
          </div>
        </form>
        </div>

      </section>

  <section v-if="activePanel === 'explorar'" class="mt-6">
        <h2 class="text-lg font-semibold mb-2">Explorar Rutinas</h2>
        <div v-if="loadingExplorar" class="bg-white p-4 rounded shadow">Cargando rutinas...</div>
        <div v-else>
          <div v-if="explorarRutinas.length === 0" class="bg-white p-4 rounded shadow">No hay rutinas públicas disponibles.</div>
          <div v-else class="bg-white p-4 rounded shadow">
            <!-- Buscar y filtros -->
            <div class="flex items-center justify-between mb-4">
              <div class="flex-1 pr-4">
                <input v-model="searchQuery" @input="onSearch" placeholder="Buscar por nombre o nivel..." class="w-full px-3 py-2 border rounded" />
              </div>
              <aside class="w-60 trainer-list">
                <h3 class="font-semibold mb-2">Entrenadores</h3>
                <div class="space-y-2">
                  <button :class="{'font-semibold text-blue-600': selectedTrainerId===null}" @click="selectTrainer(null)" class="px-2 py-1 rounded bg-gray-50 w-full text-left">Todos</button>
                  <button v-for="t in trainers" :key="t.entrenador_id" @click="selectTrainer(t.entrenador_id)" :class="{'font-semibold text-blue-600': selectedTrainerId===t.entrenador_id}" class="px-2 py-1 rounded bg-gray-50 w-full text-left">{{ t.entrenador_nombre || '—' }}</button>
                </div>
              </aside>
            </div>

            <!-- Grid de tarjetas -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div v-for="r in paginatedRutinas" :key="r.id" class="bg-white border rounded p-4 shadow hover:shadow-md">
                <div class="flex justify-between items-start">
                  <div>
                    <h3 class="font-semibold text-lg cursor-pointer" @click="openRutinaDetail(r.id)">{{ r.nombre }} <span v-if="localSavedRutinas.includes(r.id)" class="ml-2 text-xs px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded">Guardado</span></h3>
                    <div class="text-sm text-gray-600">{{ r.nivel }} • {{ r.entrenador_nombre || '—' }}</div>
                  </div>
                  <div class="text-xs text-gray-500">{{ r.creado_en ? new Date(r.creado_en).toLocaleDateString() : '' }}</div>
                </div>
                <p class="mt-3 text-sm text-gray-700">{{ r.descripcion }}</p>
                <div class="mt-4 flex items-center justify-between">
                  <button @click="openRutinaDetail(r.id)" class="px-3 py-1 bg-blue-600 text-white rounded">Ver</button>
                  <button :disabled="savingFollowIds.includes(r.id) || localSavedRutinas.includes(r.id)" @click="followRutina(r.id)" class="px-3 py-1 bg-green-600 text-white rounded">{{ savingFollowIds.includes(r.id) ? 'Guardando...' : (localSavedRutinas.includes(r.id) ? 'Guardado' : 'Guardar rutina') }}</button>
                </div>
              </div>
            </div>

            <!-- Paginación simple -->
            <div class="mt-4 flex items-center justify-center space-x-2">
              <button :disabled="page<=1" @click="page--" class="px-3 py-1 border rounded">Anterior</button>
              <div>Página {{ page }} / {{ totalPages }}</div>
              <button :disabled="page>=totalPages" @click="page++" class="px-3 py-1 border rounded">Siguiente</button>
            </div>
          </div>
        </div>
      </section>

      <section v-if="activePanel === 'misrutinas'" class="mt-6">
        <h2 class="text-lg font-semibold mb-2">Mis Rutinas Guardadas</h2>
        <div class="bg-white p-4 rounded shadow">
          <div v-if="loadingMis">Cargando tus rutinas guardadas...</div>
          <div v-else>
            <div v-if="misRutinas.length===0" class="text-sm text-gray-600">No tienes rutinas guardadas.</div>
            <ul class="mt-2 space-y-2">
                <li v-for="r in misRutinas" :key="r.id" class="p-3 border rounded bg-white flex justify-between items-center">
                <div>
                    <div class="font-semibold">{{ r.nombre }} <span v-if="(r._localOnly) || (localSavedRutinas && localSavedRutinas.includes(Number(r.id)))" class="ml-2 text-xs px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded">Guardada localmente</span></div>
                  <div class="text-sm text-gray-600">{{ r.descripcion }}</div>
                </div>
                <div class="space-x-2">
                  <button @click="openRutinaDetail(r.id)" class="px-3 py-1 bg-blue-600 text-white rounded">Ver</button>
                  <button @click="unfollowRutina(r.id)" class="px-3 py-1 bg-red-600 text-white rounded">Eliminar</button>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <section v-if="activePanel === 'planes'" class="mt-6">
        <h2 class="text-lg font-semibold mb-2">Mis Planes Nutricionales</h2>
        <div class="bg-white p-4 rounded shadow">
          <div v-if="loadingMis">Cargando tus rutinas guardadas y solicitudes...</div>
          <div v-else>
            <h3 class="font-semibold mb-2">Planes Alimenticios disponibles</h3>
            <div v-if="planesPublicos.length===0" class="text-sm text-gray-600 mb-4">No hay planes disponibles.</div>
            <ul class="space-y-2 mb-4">
              <li v-for="p in planesPublicos" :key="p.id" class="p-3 border rounded bg-gray-50">
                <div class="flex justify-between items-center">
                  <div>
                    <div class="font-semibold">{{ p.nombre }}</div>
                    <div class="text-sm text-gray-600">{{ p.descripcion }}</div>
                  </div>
                  <div class="space-x-2">
                    <button @click="openPlanDetail(p.id)" class="px-3 py-1 bg-blue-600 text-white rounded">Ver</button>
                    <button @click="solicitarPlan(p.id)" class="px-3 py-1 bg-green-600 text-white rounded">Solicitar plan</button>
                  </div>
                </div>
              </li>
            </ul>

            <h3 class="font-semibold mb-2">Solicitudes de plan</h3>
            <div v-if="misSolicitudes.length===0" class="text-sm text-gray-600">No has solicitado ningún plan aún.</div>
            <ul class="mt-2 space-y-2">
              <li v-for="s in misSolicitudes" :key="s.id" class="p-3 border rounded bg-white">
                <div class="flex justify-between items-start">
                  <div>
                    <div class="font-semibold">{{ s.rutina_nombre || ('Rutina ' + s.rutina_id) }}</div>
                    <div class="text-sm text-gray-600">Estado: {{ s.estado }} — {{ s.creado_en ? new Date(s.creado_en).toLocaleString() : '' }}</div>
                    <div v-if="s.nota" class="text-sm mt-1">Nota: {{ s.nota }}</div>
                  </div>
                  <div>
                    <button @click="openPlanFromSolicitud(s)" class="px-3 py-1 bg-blue-600 text-white rounded">Ver plan</button>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <section v-if="activePanel === 'mediciones'" class="mt-8">
        <h2 class="text-lg font-semibold mb-2">Historial de Mediciones</h2>
        <div v-if="loadingList">Cargando...</div>
        <table v-else class="min-w-full bg-white shadow rounded">
          <thead>
            <tr class="text-left">
              <th class="px-4 py-2">Fecha</th>
              <th class="px-4 py-2">Peso (kg)</th>
              <th class="px-4 py-2">Altura (cm)</th>
              <th class="px-4 py-2">Cintura (cm)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in mediciones" :key="m.id">
              <td class="px-4 py-2">{{ new Date(m.creado_en).toLocaleString() }}</td>
              <td class="px-4 py-2">{{ m.peso }}</td>
              <td class="px-4 py-2">{{ m.altura }}</td>
              <td class="px-4 py-2">{{ m.cintura }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <div class="mt-8 bg-white p-4 rounded shadow">
        <h2 class="text-lg font-semibold mb-2">Evolución de Peso</h2>
        <WeightChart :measurements="mediciones" />
      </div>

    </main>
  </div>
</template>

<script>
import WeightChart from '../components/WeightChart.vue'
import auth from '../utils/auth.js'
import api from '../utils/api.js'

export default {
  name: 'ClienteDashboard',
  components: { WeightChart },
  data() {
    return {
      peso: null,
      altura: null,
      cintura: null,
      saving: false,
      msg: '',
      mediciones: [],
      loadingList: false
      ,
      explorarRutinas: [],
      loadingExplorar: false,
      selectedTrainerId: null
      ,
      activePanel: 'mediciones',
      // UI: search + pagination
      searchQuery: '',
      page: 1,
      pageSize: 6,
      savingFollowIds: [],
      // local fallback for saved rutinas (for unauthenticated or server errors)
      localSavedRutinas: []
      ,
      // mis rutinas / solicitudes
      misRutinas: [],
      misSolicitudes: [],
      loadingMis: false
      ,
      planesPublicos: []
    }
  },
  methods: {
    async submitMedicion() {
      this.saving = true
      this.msg = ''
      try {
        const user_id = auth.getSession().user_id
        const res = await api.post('/api/mediciones', { peso: this.peso, altura: this.altura, cintura: this.cintura })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Error al guardar')
        this.msg = 'Medición guardada con id ' + data.id
        this.peso = this.altura = this.cintura = null
        // refrescar la lista
        this.fetchMediciones()
      } catch (err) {
        this.msg = err.message
      } finally {
        this.saving = false
      }
    },

    async fetchMediciones() {
      // keep fetching mediciones for the chart only
      this.loadingList = true
      this.mediciones = []
      try {
        const user_id = auth.getSession().user_id
        const res = await api.get(`/api/mediciones/${user_id}`)
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Error al obtener mediciones')
        this.mediciones = data
      } catch (err) {
        console.error(err)
      } finally {
        this.loadingList = false
      }
    },

    async fetchRutinasPublicas() {
      this.loadingExplorar = true
      this.explorarRutinas = []
      try {
        const res = await api.get('/api/rutinas/public', { skipAuth: true })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Error al obtener rutinas')
        this.explorarRutinas = data
        // load local saved ids
        try {
          const saved = JSON.parse(localStorage.getItem('saved_rutinas') || '[]')
          this.localSavedRutinas = Array.isArray(saved) ? saved : []
        } catch (e) {
          this.localSavedRutinas = []
        }
      } catch (err) {
        console.error('fetchRutinasPublicas', err)
      } finally {
        this.loadingExplorar = false
      }
    },

    selectTrainer(trainerId) {
      this.selectedTrainerId = trainerId
      this.page = 1
    },

    onSearch() {
      this.page = 1
    },

    async followRutina(rutinaId) {
      if (!rutinaId) return
      // optimistically show saving state per-rutina
      if (!this.savingFollowIds.includes(rutinaId)) this.savingFollowIds.push(rutinaId)
      try {
        const res = await api.post(`/api/rutinas/${rutinaId}/seguir`, {})
        const body = await res.json()
        if (!res.ok) throw new Error(body.error || 'Error guardando rutina')
        // success: update local marker
        if (!this.localSavedRutinas.includes(rutinaId)) {
          this.localSavedRutinas.push(rutinaId)
          localStorage.setItem('saved_rutinas', JSON.stringify(this.localSavedRutinas))
        }
        // option: show small message
        // toast.show('Rutina guardada', 2000)
      } catch (err) {
        console.error('followRutina, falling back to local save', err)
        // Fallback: save locally so user can see it in "Mis rutinas" even if server failed
        try {
          if (!this.localSavedRutinas.includes(rutinaId)) {
            this.localSavedRutinas.push(rutinaId)
            localStorage.setItem('saved_rutinas', JSON.stringify(this.localSavedRutinas))
          }
        } catch (e) {
          console.error('local save failed', e)
        }
      } finally {
        const idx = this.savingFollowIds.indexOf(rutinaId)
        if (idx !== -1) this.savingFollowIds.splice(idx, 1)
      }
    },

    async unfollowRutina(rutinaId) {
      if (!rutinaId) return
      if (!confirm('¿Eliminar esta rutina guardada?')) return
      try {
        const res = await api.del(`/api/rutinas/${rutinaId}/seguir`)
        // attempt to parse body but tolerate non-json
        let body = {}
        try { body = await res.json() } catch (e) { body = {} }
        if (!res.ok) throw new Error(body.error || 'Error eliminando rutina guardada')
        // remove from local array
        this.misRutinas = this.misRutinas.filter(r => r.id !== rutinaId)
        // also remove from localSavedRutinas if present
        try {
          this.localSavedRutinas = (this.localSavedRutinas || []).filter(id => id !== rutinaId)
          localStorage.setItem('saved_rutinas', JSON.stringify(this.localSavedRutinas))
        } catch (e) {}
      } catch (err) {
        console.error('unfollowRutina failed', err)
        try { alert('No se pudo eliminar la rutina guardada: ' + (err.message || err)) } catch (e) {}
      }
    },

    openRutinaDetail(rutinaId) {
      this.$router.push(`/cliente/rutina/${rutinaId}`)
    },

    openRutinaFromSolicitud(rutinaId) {
      // Defensive: ensure rutinaId is valid before navigating (prevents /cliente/rutina/null)
      if (!rutinaId || rutinaId === 'null' || isNaN(Number(rutinaId))) {
        // show a friendly message instead of navigating to an invalid route
        try { alert('ID de rutina inválido') } catch (e) { console.warn('ID inválido') }
        return
      }
      this.openRutinaDetail(rutinaId)
    },

    // Navegar entre paneles y sincronizar con la ruta
    select(panel) {
      if (!panel) return
      this.activePanel = panel
      // actualizar la URL para que sea shareable
      try {
        this.$router.push(`/cliente/${panel}`)
      } catch (e) {
        // ignore navigation errors
      }
      if (panel === 'mediciones') this.fetchMediciones()
      if (panel === 'explorar') this.fetchRutinasPublicas()
  if (panel === 'planes') this.fetchMisRutinas()
  if (panel === 'misrutinas') this.fetchMisRutinas()
    },

    logout() {
      auth.clearSession()
      this.$router.push('/')
    }
    ,
    async solicitarPlan(planId) {
      try {
        const res = await api.post(`/api/planes/${planId}/solicitar`, {})
        const body = await res.json()
        if (!res.ok) throw new Error(body.error || 'Error solicitando plan')
        // refresh solicitudes list
        this.fetchMisRutinas()
      } catch (err) {
        console.error('solicitarPlan failed', err)
        // fallback: store as local solicitud marker
        try {
          const local = JSON.parse(localStorage.getItem('local_solicitudes') || '[]')
          if (!local.includes(planId)) {
            local.push(planId)
            localStorage.setItem('local_solicitudes', JSON.stringify(local))
          }
          alert('Solicitud guardada localmente; se sincronizará al iniciar sesión')
        } catch (e) {
          console.error('local solicitud failed', e)
        }
      }
    },

    openPlanDetail(planId) {
      // For now reuse rutina detail route? We'll navigate to a simple route showing plan id
      this.$router.push(`/cliente/plan/${planId}`)
    },
    openPlanFromSolicitud(solicitud) {
      // solicitud is an object with possible plan_id and rutina_id
      if (!solicitud) return
      const planId = solicitud.plan_id
      const rutId = solicitud.rutina_id
      if (planId) {
        // navigate to plan detail and include solicitudId in query so the plan view
        // can offer a 'Cancelar plan' action tied to this solicitud
        this.$router.push({ path: `/cliente/plan/${planId}`, query: { solicitudId: solicitud.id } })
        return
      }
      // No plan assigned yet: show friendly info and allow user to cancel if they want
      if (rutId) {
        try { alert('Aún no hay un plan asignado a esta solicitud. Intenta más tarde o contacta con tu entrenador.') } catch (e) {}
        return
      }
      try { alert('Solicitud inválida: sin rutina ni plan asociado.') } catch (e) {}
    },
    async fetchMisRutinas() {
      this.loadingMis = true
      this.misRutinas = []
      this.misSolicitudes = []
      try {
        // saved rutinas (requires auth). If server returns none, merge with any
        // locally-saved rutina ids so the user still sees their saved items.
        try {
          const res = await api.get('/api/rutinas/mis')
          if (res && res.ok) {
            this.misRutinas = await res.json()
          }
        } catch (e) {
          console.error('fetch mis rutinas failed', e)
        }

        // Merge local saved rutinas (localStorage) as a fallback so users who
        // saved rutinas while unauthenticated or when the server failed still
        // see them in "Mis Rutinas".
        try {
          const saved = JSON.parse(localStorage.getItem('saved_rutinas') || '[]')
          this.localSavedRutinas = Array.isArray(saved) ? saved : []
        } catch (e) {
          this.localSavedRutinas = []
        }

        if ((this.localSavedRutinas || []).length > 0) {
          const existingIds = new Set((this.misRutinas || []).map(r => r.id))
          for (const rid of this.localSavedRutinas) {
            if (!existingIds.has(rid)) {
              try {
                // Attempt to fetch rutina detail (public fallback)
                const rr = await api.get(`/api/rutinas/${rid}`, { skipAuth: true })
                if (rr && rr.ok) {
                  const detail = await rr.json()
                  // mark as local-only because it wasn't returned by /api/rutinas/mis
                  detail._localOnly = true
                  this.misRutinas.push(detail)
                  existingIds.add(rid)
                } else {
                  // Create a minimal placeholder so the user sees the saved item
                  this.misRutinas.push({ id: rid, nombre: 'Rutina guardada', descripcion: '', _localOnly: true })
                  existingIds.add(rid)
                }
              } catch (err) {
                console.error('failed to fetch rutina detail for', rid, err)
                this.misRutinas.push({ id: rid, nombre: 'Rutina guardada', descripcion: '', _localOnly: true })
                existingIds.add(rid)
              }
            }
          }
        }

        // solicitudes
        try {
          const r2 = await api.get('/api/solicitudes/mis')
          if (r2 && r2.ok) {
            this.misSolicitudes = await r2.json()
          }
        } catch (e) {
          console.error('fetch mis solicitudes failed', e)
        }
        // planes publicos
        try {
          const rp = await api.get('/api/planes', { skipAuth: true })
          if (rp && rp.ok) {
            this.planesPublicos = await rp.json()
          }
        } catch (e) {
          console.error('fetch planes publicos failed', e)
        }
      } finally {
        this.loadingMis = false
      }
    }
  },
  computed: {
    trainers() {
      // build list of unique trainers from explorarRutinas
      const map = {}
      this.explorarRutinas.forEach(r => {
        const id = r.entrenador_id || ('_' + (r.entrenador_nombre || ''))
        if (!map[id]) map[id] = { entrenador_id: r.entrenador_id, entrenador_nombre: r.entrenador_nombre }
      })
      return Object.values(map)
    },
    filteredRutinas() {
      // apply trainer filter and searchQuery
      let list = this.explorarRutinas || []
      if (this.selectedTrainerId) {
        list = list.filter(r => r.entrenador_id === this.selectedTrainerId)
      }
      if (this.searchQuery && this.searchQuery.trim().length > 0) {
        const q = this.searchQuery.trim().toLowerCase()
        list = list.filter(r => (r.nombre || '').toLowerCase().includes(q) || (r.nivel || '').toLowerCase().includes(q) || (r.descripcion || '').toLowerCase().includes(q))
      }
      return list
    },
    totalPages() {
      const total = Math.max(1, Math.ceil((this.filteredRutinas || []).length / this.pageSize))
      return total
    },
    paginatedRutinas() {
      const start = (this.page - 1) * this.pageSize
      return (this.filteredRutinas || []).slice(start, start + this.pageSize)
    }
  },
  mounted() {
    const parts = (this.$route && this.$route.path) ? this.$route.path.split('/') : []
    const panel = parts[2] || 'mediciones'
    if (panel) this.activePanel = panel
    if (this.activePanel === 'mediciones') this.fetchMediciones()
    if (this.activePanel === 'explorar') this.fetchRutinasPublicas()
    this.$watch(() => this.$route.path, (newPath) => {
      const p = (newPath || '').split('/')[2] || 'mediciones'
      if (p) this.select(p)
    })
  }

    
}
</script>

<style scoped>
.trainer-list button {
  text-align: left;
  width: 100%;
}
</style>
