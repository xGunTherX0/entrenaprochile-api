import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/Login.vue'
import EntrenadorDashboard from '../views/EntrenadorDashboard.vue'
import ClienteDashboard from '../views/ClienteDashboard.vue'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: Login
  }
  ,{
    path: '/entrenador',
    name: 'Entrenador',
    component: EntrenadorDashboard
  },
  {
    path: '/cliente',
    name: 'Cliente',
    component: ClienteDashboard
  },
  {
    path: '/home',
    name: 'Home',
    component: Home
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
