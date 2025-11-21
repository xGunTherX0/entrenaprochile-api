import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/Login.vue'
import EntrenadorDashboard from '../views/EntrenadorDashboard.vue'
import EntrenadorAprobar from '../views/EntrenadorAprobar.vue'
import ClienteDashboard from '../views/ClienteDashboard.vue'
import ClienteRutina from '../views/ClienteRutina.vue'
import Home from '../views/Home.vue'
import Admin from '../views/Admin.vue'
// Admin child panels
import AdminUsuarios from '../views/admin/Usuarios.vue'
import AdminMetricas from '../views/admin/Metricas.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/login', name: 'Login', component: Login },

  { path: '/entrenador', redirect: '/entrenador/rutinas' },
  { path: '/entrenador/rutinas', name: 'EntrenadorRutinas', component: EntrenadorDashboard },
  { path: '/entrenador/planes', name: 'EntrenadorPlanes', component: EntrenadorDashboard },
  { path: '/entrenador/aceptados', name: 'EntrenadorAceptados', component: EntrenadorDashboard },
  { path: '/entrenador/publicar', name: 'EntrenadorPublicar', component: EntrenadorDashboard },
  { path: '/entrenador/perfil', name: 'EntrenadorPerfil', component: EntrenadorDashboard },
  { path: '/entrenador/aprobar', name: 'EntrenadorAprobar', component: EntrenadorAprobar },

  {
    path: '/cliente',
    name: 'Cliente',
    component: () => import('../views/ClienteLayout.vue'),
    redirect: '/cliente/mediciones',
    children: [
      { path: 'mediciones', name: 'ClienteMediciones', component: () => import('../views/ClienteMediciones.vue') },
      { path: 'explorar', name: 'ClienteExplorar', component: () => import('../views/ExplorarRutinas.vue') },
  { path: 'explorar-planes', name: 'ClienteExplorarPlanes', component: () => import('../views/ExplorarPlanes.vue') },
      { path: 'misrutinas', name: 'ClienteMisRutinas', component: () => import('../views/MisRutinas.vue') },
      { path: 'rutina/:id', name: 'ClienteRutina', component: () => import('../views/ClienteRutina.vue'), props: true },
      { path: 'plan/:id', name: 'ClientePlan', component: () => import('../views/ClientePlan.vue'), props: true },
      { path: 'planes', name: 'ClientePlanes', component: () => import('../views/MisPlanes.vue') },
      // Entrenadores dentro del layout de Cliente para que el panel lateral siempre se muestre
      { path: 'entrenadores', name: 'ClienteExplorarEntrenadores', component: () => import('../views/ExplorarEntrenadores.vue') },
      // Keep the global route name 'EntrenadorPublico' so existing links using that
      // name continue to resolve, but the component will render inside ClienteLayout.
      { path: 'entrenadores/:id', name: 'EntrenadorPublico', component: () => import('../views/EntrenadorPublico.vue'), props: true }
    ]
  },

  { path: '/home', name: 'Home', component: Home },
  // Keep legacy top-level routes but redirect to the cliente-layout variants
  { path: '/entrenadores', redirect: '/cliente/entrenadores' },
  { path: '/entrenadores/:id', redirect: to => `/cliente/entrenadores/${to.params.id}` },

  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    redirect: '/admin/usuarios',
    children: [
      { path: 'usuarios', name: 'AdminUsuarios', component: AdminUsuarios },
      { path: 'review', name: 'AdminReview', component: () => import('../views/admin/AdminReview.vue') },
      { path: 'entrenadores', name: 'AdminTrainers', component: () => import('../views/admin/AdminTrainers.vue') },
      { path: 'aceptados', redirect: 'review' },
      { path: 'usuarios/:id', name: 'AdminUsuarioPerfil', component: () => import('../views/admin/UsuarioPerfil.vue'), props: true },
      { path: 'metricas', name: 'AdminMetricas', component: AdminMetricas }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Rutas protegidas: cualquiera que no sea login ('/') requiere sesión
const protectedPrefixes = ['/entrenador', '/cliente', '/admin', '/home']

import auth from '../utils/auth.js'

router.beforeEach((to, from, next) => {
  // If route is protected, require a valid auth token + user info in localStorage
  if (protectedPrefixes.some(p => to.path.startsWith(p))) {
    const token = auth.getAuthToken()
    const role = auth.getRole()
    const userId = localStorage.getItem('user_id')
    if (!token || !role || !userId) {
      // No logueado -> redirigir al login
      return next({ path: '/' })
    }
  }

  // If user is at login page but already has a token, you may redirect them
  // to their landing page (optional). We'll keep default behavior (show login)
  next()
})

export default router
