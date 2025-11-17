<template>
  <div class="min-h-screen flex bg-gray-50">
    <nav class="w-64 bg-white border-r p-4">
      <h2 class="text-xl font-bold mb-4">Entrenador</h2>
      <ul>
        <li class="mb-2"><button @click="select('rutinas')" :class="{'text-blue-600 font-semibold': activePanel==='rutinas'}" class="text-left w-full">Mis Rutinas</button></li>
        <li class="mb-2"><button @click="select('planes')" :class="{'text-blue-600 font-semibold': activePanel==='planes'}" class="text-left w-full">Mis Planes Alimenticios</button></li>
        <li class="mb-2"><button @click="select('aceptados')" :class="{'text-blue-600 font-semibold': activePanel==='aceptados'}" class="text-left w-full">Solicitudes Aceptadas</button></li>
        <li class="mb-2"><button @click="select('publicar')" :class="{'text-blue-600 font-semibold': activePanel==='publicar'}" class="text-left w-full">Publicar Contenido</button></li>
        <li class="mb-2"><button @click="select('perfil')" :class="{'text-blue-600 font-semibold': activePanel==='perfil'}" class="text-left w-full">Perfil</button></li>
      </ul>
      <div class="mt-6">
        <button @click="logout" class="px-3 py-2 bg-red-500 text-white rounded">Cerrar Sesión</button>
      </div>
    </nav>
    <main class="flex-1 p-6">
      <h1 class="text-2xl font-bold">Entrenador Dashboard</h1>

      <section v-if="activePanel === 'rutinas'" class="mt-4">
        <h2 class="text-xl font-semibold mb-2">Crear nueva Rutina</h2>
        <form @submit.prevent="createRutina" class="space-y-3 bg-white p-4 rounded shadow-sm max-w-lg">
          <div>
            <label class="block text-sm font-medium">Nombre</label>
            <input v-model="form.nombre" class="mt-1 block w-full border rounded px-2 py-1" required />
          </div>
          <div>
            <label class="block text-sm font-medium">Descripción</label>
            <textarea v-model="form.descripcion" class="mt-1 block w-full border rounded px-2 py-1"></textarea>
          </div>
          <div>
            <label class="block text-sm font-medium">Nivel</label>
            <select v-model="form.nivel" class="mt-1 block w-full border rounded px-2 py-1">
              <option value="Básico">Básico</option>
              <option value="Intermedio">Intermedio</option>
              <option value="Avanzado">Avanzado</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium">Objetivo Principal</label>
            <textarea v-model="form.objetivo_principal" class="mt-1 block w-full border rounded px-2 py-1" rows="2"></textarea>
          </div>
          <div>
            <label class="block text-sm font-medium">Enfoque de la Rutina</label>
            <textarea v-model="form.enfoque_rutina" class="mt-1 block w-full border rounded px-2 py-1" rows="2"></textarea>
          </div>
          <div>
            <label class="block text-sm font-medium">Enlace externo (URL)</label>
            <input v-model="form.link_url" placeholder="https://..." class="mt-1 block w-full border rounded px-2 py-1" />
          </div>
          <!-- Removed deprecated fields: Cualidades Clave, Duración y Frecuencia,
               Material Requerido, Instrucciones Estructurales (no longer part of create form) -->
          <!-- Removed create-time 'Es pública' checkbox: new content goes to review -->
          <div>
            <button type="submit" class="px-3 py-2 bg-green-600 text-white rounded">Crear Rutina</button>
          </div>
        </form>

  <h2 class="text-xl font-semibold mt-6 mb-2">Mis Rutinas</h2>
        <div class="bg-white p-4 rounded shadow-sm">
          <table class="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th class="px-4 py-2 text-left">Nombre</th>
                <th class="px-4 py-2 text-left">Descripción</th>
                <th class="px-4 py-2 text-left">Nivel</th>
                <th class="px-4 py-2 text-left">Objetivo</th>
                <th class="px-4 py-2 text-left">Enfoque</th>
                      <th class="px-4 py-2 text-left">Enlace</th>
                <!-- Removed columns: Cualidades, Duración, Material, Instrucciones -->
                <th class="px-4 py-2 text-left">Pública</th>
                <th class="px-4 py-2 text-left">Creado</th>
                <th class="px-4 py-2 text-left">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rutinas" :key="r.id" class="border-t">
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id" class="font-semibold">{{ r.nombre }}</div>
                  <div v-else>
                    <input v-model="editForm.nombre" class="border px-2 py-1 w-full" />
                  </div>
                </td>
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id">{{ r.descripcion || '-' }}</div>
                  <div v-else>
                    <textarea v-model="editForm.descripcion" class="border px-2 py-1 w-full" rows="2"></textarea>
                  </div>
                </td>
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id">{{ r.nivel }}</div>
                  <div v-else>
                    <select v-model="editForm.nivel" class="border px-2 py-1">
                      <option value="Básico">Básico</option>
                      <option value="Intermedio">Intermedio</option>
                      <option value="Avanzado">Avanzado</option>
                    </select>
                  </div>
                </td>
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id">{{ r.objetivo_principal || '-' }}</div>
                  <div v-else>
                    <textarea v-model="editForm.objetivo_principal" class="border px-2 py-1 w-full" rows="2"></textarea>
                  </div>
                </td>
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id">{{ r.enfoque_rutina || '-' }}</div>
                  <div v-else>
                    <textarea v-model="editForm.enfoque_rutina" class="border px-2 py-1 w-full" rows="2"></textarea>
                  </div>
                </td>
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id">
                    <div v-if="r.link_url"><a :href="r.link_url" target="_blank" class="text-blue-600 underline text-sm">Abrir</a></div>
                    <div v-else class="text-sm text-gray-500">-</div>
                  </div>
                  <div v-else>
                    <input v-model="editForm.link_url" class="border px-2 py-1 w-full" placeholder="https://..." />
                  </div>
                </td>
                <!-- Removed Cualidades/Duración/Material/Instrucciones columns from table and edit form -->
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id">{{ r.es_publica ? 'Sí' : 'No' }}</div>
                  <div v-else>
                    <input type="checkbox" v-model="editForm.es_publica" />
                  </div>
                </td>
                <td class="px-4 py-2">{{ formatDate(r.creado_en) }}</td>
                <td class="px-4 py-2">
                  <div v-if="editingId !== r.id" class="space-x-2">
                    <button @click="startEdit(r)" class="px-2 py-1 bg-yellow-400 text-white rounded">Editar</button>
                    <button @click="deleteRutina(r.id)" class="px-2 py-1 bg-red-600 text-white rounded">Eliminar</button>
                  </div>
                  <div v-else class="space-x-2">
                    <button @click="saveEdit(r.id)" class="px-2 py-1 bg-green-600 text-white rounded">Guardar</button>
                    <button @click="cancelEdit" class="px-2 py-1 bg-gray-300 rounded">Cancelar</button>
                  </div>
                </td>
              </tr>
              <tr v-if="!rutinas.length">
                <td class="px-4 py-2" colspan="9">No hay rutinas aún.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-if="activePanel === 'planes'" class="mt-4">
        <h2 class="text-xl font-semibold">Mis Planes Alimenticios</h2>
        <div class="bg-white p-4 rounded shadow-sm max-w-xl">
          <form @submit.prevent="createPlan" class="space-y-3">
            <div>
              <label class="block text-sm font-medium">Nombre</label>
              <input v-model="planForm.nombre" class="mt-1 block w-full border rounded px-2 py-1" required />
            </div>
            <div>
              <label class="block text-sm font-medium">Descripción</label>
              <textarea v-model="planForm.descripcion" class="mt-1 block w-full border rounded px-2 py-1"></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium">Contenido</label>
              <textarea v-model="planForm.contenido" class="mt-1 block w-full border rounded px-2 py-1" placeholder="Ej: Desayuno, Almuerzo, Cena"></textarea>
            </div>
            <!-- Removed create-time 'Es público' checkbox: new plans go to review -->
            <div>
              <button type="submit" class="px-3 py-2 bg-green-600 text-white rounded">Crear Plan</button>
            </div>
          </form>

          <h3 class="text-lg font-semibold mt-6">Tus planes</h3>
          <div v-if="misPlanes.length" class="mt-2 space-y-3">
            <div v-for="p in misPlanes" :key="p.id" class="border rounded p-3 bg-gray-50">
              <div class="flex justify-between items-start">
                <div>
                  <div v-if="editingPlanId !== p.id" class="font-semibold">{{ p.nombre }}</div>
                  <div v-else>
                    <input v-model="planEditForm.nombre" class="border px-2 py-1 w-full" />
                  </div>
                  <div class="text-sm text-gray-600">{{ formatDate(p.creado_en) }}</div>
                </div>
                <div class="text-right text-sm">
                  <div v-if="editingPlanId !== p.id">{{ p.es_publico ? 'Público' : (p.es_publico === false ? 'Pendiente' : 'Privado') }}</div>
                  <div v-else><input type="checkbox" v-model="planEditForm.es_publico" /> Público</div>
                </div>
              </div>
              <div class="mt-2 text-sm text-gray-700">
                <div v-if="editingPlanId !== p.id">{{ p.descripcion }}</div>
                <div v-else><textarea v-model="planEditForm.descripcion" class="w-full border px-2 py-1"></textarea></div>
              </div>
              <div class="mt-2 text-xs text-gray-600">
                <div v-if="editingPlanId !== p.id">{{ p.contenido }}</div>
                <div v-else><textarea v-model="planEditForm.contenido" class="w-full border px-2 py-1"></textarea></div>
              </div>
              <div class="mt-3 flex justify-end space-x-2">
                <template v-if="editingPlanId !== p.id">
                  <button @click="startEditPlan(p)" class="px-2 py-1 bg-yellow-400 text-white rounded">Editar</button>
                  <button @click="togglePublicPlan(p)" class="px-2 py-1 bg-blue-600 text-white rounded">Toggle Público</button>
                  <button @click="deletePlan(p.id)" class="px-2 py-1 bg-red-600 text-white rounded">Eliminar</button>
                </template>
                <template v-else>
                  <button @click="saveEditPlan(p.id)" class="px-2 py-1 bg-green-600 text-white rounded">Guardar</button>
                  <button @click="cancelEditPlan" class="px-2 py-1 bg-gray-300 rounded">Cancelar</button>
                </template>
              </div>
            </div>
          </div>
          <div v-else class="mt-2 text-sm text-gray-600">No hay planes aún.</div>
        </div>
      </section>

      <section v-if="activePanel === 'publicar'" class="mt-4">
        <h2 class="text-xl font-semibold">Publicar Contenido</h2>
        <div class="bg-white p-4 rounded shadow-sm">
          <h3 class="font-semibold mb-3">Solicitudes pendientes</h3>
          <div v-if="loadingSolicitudes" class="text-gray-500">Cargando solicitudes...</div>
          <div v-else>
            <div v-if="!solicitudesPendientes.length" class="text-sm text-gray-600">No hay solicitudes pendientes.</div>
            <ul v-else class="space-y-3">
              <li v-for="s in solicitudesPendientes" :key="s.id" class="border rounded p-3 bg-gray-50 flex justify-between items-start">
                <div>
                  <div class="font-semibold">{{ s.rutina_nombre || s.plan_nombre || 'Solicitud #' + s.id }}</div>
                  <div class="text-sm text-gray-600">Tipo: {{ s.rutina_id ? 'Rutina' : (s.plan_id ? 'Plan' : 'Desconocido') }} • Creado: {{ formatDate(s.creado_en) }}</div>
                  <div v-if="s.cliente_nombre" class="text-sm text-gray-700 mt-1">Solicitado por: <span class="font-medium">{{ s.cliente_nombre }}</span></div>
                  <div v-else-if="s.cliente_id" class="text-sm text-gray-700 mt-1">Solicitado por cliente id: <span class="font-medium">{{ s.cliente_id }}</span></div>
                  <div v-if="s.nota" class="mt-2 text-sm">Nota: {{ s.nota }}</div>
                </div>
                <div class="space-x-2">
                  <button :disabled="actionLoading[s.id]" @click="aceptarSolicitud(s.id)" class="px-3 py-1 bg-green-600 text-white rounded">Aceptar</button>
                  <button :disabled="actionLoading[s.id]" @click="rechazarSolicitud(s.id)" class="px-3 py-1 bg-red-600 text-white rounded">Rechazar</button>
                </div>
              </li>
            </ul>
          </div>
          <div v-if="publicarMessage" class="mt-3 text-sm text-green-600">{{ publicarMessage }}</div>
          <div v-if="publicarError" class="mt-3 text-sm text-red-600">{{ publicarError }}</div>
        </div>
      </section>

      <section v-if="activePanel === 'aceptados'" class="mt-4">
        <h2 class="text-xl font-semibold">Mis Contenidos Aceptados</h2>
        <div class="bg-white p-4 rounded shadow-sm">
          <div v-if="loadingAceptados" class="text-gray-500">Cargando...</div>
          <div v-else-if="errorAceptados" class="text-red-600">{{ errorAceptados }}</div>
          <div v-else>
            <h3 class="font-semibold">Rutinas</h3>
            <div v-if="!aceptados.rutinas || !aceptados.rutinas.length" class="text-sm text-gray-600">No hay rutinas.</div>
            <ul v-else class="mt-2 space-y-2">
              <li v-for="r in aceptados.rutinas" :key="r.id" class="p-3 border rounded">
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
                    <li v-for="c in r.accepted_clients" :key="'r-'+c.cliente_id">{{ c.nombre || ('cliente '+c.cliente_id) }} (usuario: {{ c.usuario_id }})</li>
                  </ul>
                </div>
              </li>
            </ul>

            <h3 class="font-semibold mt-4">Planes</h3>
            <div v-if="!aceptados.planes || !aceptados.planes.length" class="text-sm text-gray-600">No hay planes.</div>
            <ul v-else class="mt-2 space-y-2">
              <li v-for="p in aceptados.planes" :key="p.id" class="p-3 border rounded">
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
      </section>
      
      <section v-if="activePanel === 'perfil'" class="mt-4">
        <h2 class="text-xl font-semibold">Perfil de Entrenador</h2>
        <div class="bg-white p-4 rounded shadow-sm max-w-2xl">
          <div v-if="loadingProfile" class="text-gray-500">Cargando perfil...</div>
          <div v-else>
            <div class="mb-3">
              <label class="block text-sm text-gray-600">Nombre</label>
              <input v-model="profile.nombre" class="mt-1 block w-full border rounded px-2 py-1" />
            </div>
            <div class="mb-3">
              <label class="block text-sm text-gray-600">Email</label>
              <input v-model="profile.email" disabled class="mt-1 block w-full border rounded px-2 py-1 bg-gray-100" />
            </div>
            <div class="mb-3">
              <label class="block text-sm text-gray-600">Especialidad</label>
              <input v-model="profile.speciality" class="mt-1 block w-full border rounded px-2 py-1" />
            </div>
            <div class="mb-3">
              <label class="block text-sm text-gray-600">Teléfono</label>
              <input v-model="profile.telefono" class="mt-1 block w-full border rounded px-2 py-1" />
            </div>
            <div class="mb-3">
              <label class="block text-sm text-gray-600">Biografía</label>
              <textarea v-model="profile.bio" class="mt-1 block w-full border rounded px-2 py-1" rows="4"></textarea>
            </div>
            <div class="mb-3">
              <label class="block text-sm text-gray-600">Instagram (URL)</label>
              <input v-model="profile.instagram_url" placeholder="https://instagram.com/tu_usuario" class="mt-1 block w-full border rounded px-2 py-1" />
            </div>
            <div class="mb-3">
              <label class="block text-sm text-gray-600">YouTube (URL)</label>
              <input v-model="profile.youtube_url" placeholder="https://youtube.com/channel/tu_canal" class="mt-1 block w-full border rounded px-2 py-1" />
            </div>
            <div class="flex justify-end">
              <button @click="saveProfile" class="px-3 py-2 bg-blue-600 text-white rounded">Guardar Perfil</button>
            </div>
            <div v-if="profileMessage" class="mt-3 text-sm text-green-600">{{ profileMessage }}</div>
            <div v-if="profileError" class="mt-3 text-sm text-red-600">{{ profileError }}</div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
import auth from '../utils/auth.js'
import api from '../utils/api.js'

export default {
  name: 'EntrenadorDashboard',
  data() {
    return {
      form: {
        nombre: '',
        descripcion: '',
        objetivo_principal: '',
        enfoque_rutina: '',
        nivel: 'Básico',
        es_publica: false,
        link_url: ''
      },
      rutinas: []
      ,
      activePanel: 'rutinas',
      // editing state for rutinas
      editingId: null,
      editForm: { nombre: '', descripcion: '', objetivo_principal: '', enfoque_rutina: '', nivel: 'Básico', es_publica: false, link_url: '' },
      // plan form state declared here so Vue reactivity works
      planForm: { nombre: '', descripcion: '', contenido: '', es_publico: false },
      misPlanes: [],
      profile: { nombre: '', email: '', speciality: '', bio: '', telefono: '', instagram_url: '', youtube_url: '' },
      loadingProfile: false,
      profileError: null,
      profileMessage: null,
      // editing state for plans
      editingPlanId: null,
      planEditForm: { nombre: '', descripcion: '', contenido: '', es_publico: false }
      ,
      // solicitudes (for publicar content)
      solicitudesPendientes: [],
      loadingSolicitudes: false,
      actionLoading: {},
      publicarMessage: null,
      publicarError: null
      ,
      // aceptados
      aceptados: { rutinas: [], planes: [] },
      loadingAceptados: false,
      errorAceptados: null
    }
  },
  methods: {
    logout() {
      auth.clearSession()
      this.$router.push('/')
    },

    select(panel) {
      try { this.$router.push(`/entrenador/${panel}`) } catch (e) {}
      this.activePanel = panel
      // load data for the selected panel
      if (panel === 'rutinas') {
        this.fetchRutinas()
      } else if (panel === 'planes') {
        this.fetchMisPlanes()
      } else if (panel === 'aceptados') {
        this.fetchAceptados()
      } else if (panel === 'publicar') {
        this.fetchSolicitudesPendientes()
      } else if (panel === 'perfil') {
        this.loadProfile()
      }
    },

      async fetchAceptados() {
        this.loadingAceptados = true
        this.errorAceptados = null
        try {
          const res = await api.get('/api/entrenador/aceptados')
          if (!res.ok) {
            const j = await res.json().catch(() => ({}))
            this.errorAceptados = j.error || `Error cargando aceptados (${res.status})`
            this.aceptados = { rutinas: [], planes: [] }
            return
          }
          this.aceptados = await res.json()
        } catch (e) {
          this.errorAceptados = e.message || String(e)
          this.aceptados = { rutinas: [], planes: [] }
        } finally {
          this.loadingAceptados = false
        }
      },

    async fetchRutinas() {
      const session = auth.getSession()
      if (!session.user_id) return
      try {
        const res = await api.get(`/api/rutinas/${session.user_id}`)
        if (!res.ok) {
          // try to parse JSON error body for diagnostics
          let body = null
          try { body = await res.json() } catch (e) { body = await res.text().catch(() => null) }
          console.error('fetchRutinas server error', res.status, body)
          alert('Error al obtener rutinas del servidor:\n' + JSON.stringify(body))
          return
        }
        const data = await res.json()
        this.rutinas = Array.isArray(data) ? data : []
      } catch (e) {
        console.error('fetchRutinas', e)
      }
    },

    async fetchMisPlanes() {
      try {
        const res = await api.get('/api/planes/mis')
        if (!res || !res.ok) {
          // non-fatal: leave misPlanes empty and log
          const body = res && res.json ? await res.json().catch(() => ({})) : null
          console.error('fetchMisPlanes server error', res && res.status, body)
          this.misPlanes = []
          return
        }
        const data = await res.json()
        this.misPlanes = Array.isArray(data) ? data : []
      } catch (e) {
        console.error('fetchMisPlanes', e)
        this.misPlanes = []
      }
    },

    async createPlan() {
      const session = auth.getSession()
      if (!session || !session.user_id) {
        alert('No autenticado')
        return
      }
      try {
        const payload = { ...this.planForm }
        const res = await api.post('/api/planes', payload)
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          // Mostrar el detalle completo del error para depuración (incluye received_keys/raw_body_length)
          console.error('createPlan error detail:', err)
          alert('Error creando plan (ver consola para detalle)\n' + JSON.stringify(err))
          return
        }
        // reset form and refresh list
        this.planForm = { nombre: '', descripcion: '', contenido: '', es_publico: false }
        await this.fetchMisPlanes()
        try { alert('Plan creado y enviado a revisión. Un administrador deberá aprobarlo para que sea público.') } catch(e) {}
      } catch (e) {
        console.error('createPlan', e)
        alert('Error creando plan')
      }
    },

    // Plan CRUD: delete, edit, save
    async deletePlan(id) {
      if (!confirm('¿Eliminar plan?')) return
      try {
        const res = await api.del(`/api/planes/${id}`)
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          alert('Error: ' + (err.error || JSON.stringify(err)))
          return
        }
        await this.fetchMisPlanes()
      } catch (e) {
        console.error('deletePlan', e)
        alert('Error eliminando plan')
      }
    },

    startEditPlan(p) {
      this.editingPlanId = p.id
      this.planEditForm = { nombre: p.nombre || '', descripcion: p.descripcion || '', contenido: p.contenido || '', es_publico: !!p.es_publico }
    },

    cancelEditPlan() {
      this.editingPlanId = null
      this.planEditForm = { nombre: '', descripcion: '', contenido: '', es_publico: false }
    },

    async saveEditPlan(id) {
      try {
        const res = await api.put(`/api/planes/${id}`, this.planEditForm)
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          alert('Error: ' + (err.error || JSON.stringify(err)))
          return
        }
        // Update local plan entry for faster UX instead of refetching
        try {
          const idx = this.misPlanes.findIndex(p => p.id === id)
          if (idx !== -1) {
            this.misPlanes.splice(idx, 1, { ...this.misPlanes[idx], nombre: this.planEditForm.nombre, descripcion: this.planEditForm.descripcion, contenido: this.planEditForm.contenido, es_publico: !!this.planEditForm.es_publico })
          }
        } catch (e) {
          await this.fetchMisPlanes()
        }
        this.cancelEditPlan()
      } catch (e) {
        console.error('saveEditPlan', e)
        alert('Error actualizando plan')
      }
    },

    async togglePublicPlan(p) {
      try {
        const res = await api.put(`/api/planes/${p.id}`, { es_publico: !p.es_publico })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          alert('Error: ' + (err.error || JSON.stringify(err)))
          return
        }
        // update local state immediately for snappier UI
        try { p.es_publico = !p.es_publico } catch (e) { await this.fetchMisPlanes() }
      } catch (e) {
        console.error('togglePublicPlan', e)
        alert('Error actualizando plan')
      }
    },

    formatDate(iso) {
      try { return new Date(iso).toLocaleString() } catch { return iso }
    },

    async createRutina() {
      const session = auth.getSession()
      if (!session.user_id) {
        alert('No autenticado')
        return
      }
      const payload = { ...this.form, entrenador_id: session.user_id }
      try {
        const res = await api.post('/api/rutinas', payload)
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          console.error('createRutina error detail:', err)
          alert('Error creando rutina (ver consola para detalle)\n' + JSON.stringify(err))
          return
        }
        // reset form and refresh list
        this.form = { nombre: '', descripcion: '', objetivo_principal: '', enfoque_rutina: '', nivel: 'Básico', es_publica: false, link_url: '' }
        await this.fetchRutinas()
        try { alert('Rutina creada y enviada a revisión. Un administrador deberá aprobarla para que sea pública.') } catch(e) {}
      } catch (e) {
        console.error('createRutina', e)
        alert('Error creando rutina')
      }
    },

    async loadProfile() {
      this.profileError = null
      this.profileMessage = null
      this.loadingProfile = true
      try {
        const res = await api.get('/api/entrenador/perfil')
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.profileError = j.error || `Error cargando perfil (${res.status})`
          return
        }
        const j = await res.json()
        this.profile = { nombre: j.nombre || '', email: j.email || '', speciality: j.speciality || '', bio: j.bio || '', telefono: j.telefono || '', instagram_url: j.instagram_url || '', youtube_url: j.youtube_url || '' }
      } catch (e) {
        this.profileError = e.message || String(e)
      } finally {
        this.loadingProfile = false
      }
    },

    async saveProfile() {
      this.profileError = null
      this.profileMessage = null
      try {
        const payload = { speciality: this.profile.speciality, bio: this.profile.bio, telefono: this.profile.telefono, instagram_url: this.profile.instagram_url, youtube_url: this.profile.youtube_url }
        const res = await api.put('/api/entrenador/perfil', payload)
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.profileError = j.error || 'Error guardando perfil'
          return
        }
        this.profileMessage = 'Perfil guardado.'
      } catch (e) {
        this.profileError = e.message || String(e)
      }
    },

    /* Solicitudes management */
    async fetchSolicitudesPendientes() {
      this.publicarError = null
      this.publicarMessage = null
      this.loadingSolicitudes = true
      try {
        const res = await api.get('/api/solicitudes/pendientes')
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.publicarError = j.error || `Error cargando solicitudes (${res.status})`
          this.solicitudesPendientes = []
          return
        }
        const j = await res.json()
        this.solicitudesPendientes = Array.isArray(j) ? j : []
      } catch (e) {
        this.publicarError = e.message || String(e)
        this.solicitudesPendientes = []
      } finally {
        this.loadingSolicitudes = false
      }
    },

    async aceptarSolicitud(id) {
      this.publicarError = null
      this.publicarMessage = null
      this.actionLoading[id] = true
      try {
        const res = await api.put(`/api/solicitudes/${id}`, { estado: 'aceptado' })
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.publicarError = j.error || `Error actualizando solicitud (${res.status})`
          return
        }
        this.publicarMessage = 'Solicitud aceptada.'
        // remove from list
        this.solicitudesPendientes = this.solicitudesPendientes.filter(s => s.id !== id)
      } catch (e) {
        this.publicarError = e.message || String(e)
      } finally {
        this.actionLoading[id] = false
      }
    },

    async rechazarSolicitud(id) {
      this.publicarError = null
      this.publicarMessage = null
      this.actionLoading[id] = true
      try {
        const res = await api.put(`/api/solicitudes/${id}`, { estado: 'rechazado' })
        if (!res.ok) {
          const j = await res.json().catch(() => ({}))
          this.publicarError = j.error || `Error actualizando solicitud (${res.status})`
          return
        }
        this.publicarMessage = 'Solicitud rechazada.'
        this.solicitudesPendientes = this.solicitudesPendientes.filter(s => s.id !== id)
      } catch (e) {
        this.publicarError = e.message || String(e)
      } finally {
        this.actionLoading[id] = false
      }
    },

    // Edit/Delete handlers
    async deleteRutina(id) {
      if (!confirm('¿Eliminar rutina?')) return
      const session = auth.getSession()
      try {
        const res = await api.del(`/api/rutinas/${id}`)
        if (!res.ok) {
          const err = await res.json()
          alert('Error: ' + (err.error || JSON.stringify(err)))
          return
        }
        await this.fetchRutinas()
      } catch (e) {
        console.error('deleteRutina', e)
        alert('Error eliminando rutina')
      }
    },

    startEdit(r) {
      this.editingId = r.id
      this.editForm = { nombre: r.nombre, descripcion: r.descripcion || '', objetivo_principal: r.objetivo_principal || '', enfoque_rutina: r.enfoque_rutina || '', nivel: r.nivel, es_publica: !!r.es_publica, link_url: r.link_url || '' }
    },

    cancelEdit() {
      this.editingId = null
      this.editForm = { nombre: '', descripcion: '', objetivo_principal: '', enfoque_rutina: '', nivel: 'Básico', es_publica: false, link_url: '' }
    },

    async saveEdit(id) {
      const session = auth.getSession()
      try {
        const res = await api.put(`/api/rutinas/${id}`, this.editForm)
        if (!res.ok) {
          const err = await res.json()
          alert('Error: ' + (err.error || JSON.stringify(err)))
          return
        }
        // Update the local list immediately to avoid a full refetch (faster UX)
        try {
          const idx = this.rutinas.findIndex(r => r.id === id)
          if (idx !== -1) {
            this.rutinas.splice(idx, 1, { ...this.rutinas[idx], nombre: this.editForm.nombre, descripcion: this.editForm.descripcion, objetivo_principal: this.editForm.objetivo_principal, enfoque_rutina: this.editForm.enfoque_rutina, nivel: this.editForm.nivel, es_publica: !!this.editForm.es_publica, link_url: this.editForm.link_url })
          }
        } catch (e) {
          // If in-place update fails, fallback to refetch
          await this.fetchRutinas()
        }
        this.cancelEdit()
      } catch (e) {
        console.error('saveEdit', e)
        alert('Error actualizando rutina')
      }
    }
  },
  created() {
    this.editingId = null
    this.editForm = { nombre: '', descripcion: '', objetivo_principal: '', enfoque_rutina: '', nivel: 'Básico', es_publica: false, link_url: '' }
    // plan form state
    this.planForm = { nombre: '', descripcion: '', contenido: '', es_publico: false }
    this.misPlanes = []
  },
  mounted() {
    // initialize from route path (e.g. /entrenador/rutinas)
    const parts = (this.$route && this.$route.path) ? this.$route.path.split('/') : []
    const panel = parts[2] || 'rutinas'
    if (panel) this.activePanel = panel
  if (this.activePanel === 'rutinas') this.fetchRutinas()
  if (this.activePanel === 'planes') this.fetchMisPlanes()
  if (this.activePanel === 'aceptados') this.fetchAceptados()
  if (this.activePanel === 'perfil') this.loadProfile()
  if (this.activePanel === 'publicar') this.fetchSolicitudesPendientes()
    this.$watch(() => this.$route.path, (newPath) => {
      const p = (newPath || '').split('/')[2] || 'rutinas'
      if (p) this.select(p)
    })
  }
}
</script>
