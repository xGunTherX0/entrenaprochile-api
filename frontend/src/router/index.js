import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/Login.vue'
import EntrenadorDashboard from '../views/EntrenadorDashboard.vue'
import ClienteDashboard from '../views/ClienteDashboard.vue'
import Home from '../views/Home.vue'
import Admin from '../views/Admin.vue'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: Login
  }
  ,{
    path: '/entrenador',
    redirect: '/entrenador/rutinas'
  },
  {
    path: '/entrenador/rutinas',
    name: 'EntrenadorRutinas',
    component: EntrenadorDashboard
  },
  {
    path: '/entrenador/planes',
    name: 'EntrenadorPlanes',
    component: EntrenadorDashboard
  },
  {
    path: '/entrenador/publicar',
    name: 'EntrenadorPublicar',
    component: EntrenadorDashboard
  },
  {
    path: '/cliente',
    redirect: '/cliente/mediciones'
  },
  {
    path: '/cliente/mediciones',
    name: 'ClienteMediciones',
    component: ClienteDashboard
  },
  {
    path: '/cliente/explorar',
    name: 'ClienteExplorar',
    component: ClienteDashboard
  },
  {
    path: '/cliente/planes',
    name: 'ClientePlanes',
    component: ClienteDashboard
  },
  {
    path: '/home',
    name: 'Home',
    component: Home
  }
  ,{
    path: '/admin',
    redirect: '/admin/usuarios'
  },
  {
    path: '/admin/usuarios',
    name: 'AdminUsuarios',
    component: Admin
  },
  {
    path: '/admin/metricas',
    name: 'AdminMetricas',
    component: Admin
  },
  {
    path: '/admin/aprobar',
    name: 'AdminAprobar',
    component: Admin
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Rutas protegidas: cualquiera que no sea login ('/') requiere sesión
const protectedPrefixes = ['/entrenador', '/cliente', '/admin', '/home']

router.beforeEach((to, from, next) => {
  if (protectedPrefixes.some(p => to.path.startsWith(p))) {
    const role = localStorage.getItem('user_role')
    const userId = localStorage.getItem('user_id')
    if (!role || !userId) {
      // No logueado -> redirigir al login
      return next({ path: '/' })
    }
  }
  next()
})

export default router
