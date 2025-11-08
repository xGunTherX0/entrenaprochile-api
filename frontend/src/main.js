import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/tailwind.css'
import auth from './utils/auth.js'
import toast from './utils/toast.js'

// Global fetch wrapper: intercept 401/403 responses, clear session and redirect to login.
// This avoids duplicating 401 handling across components.
const _originalFetch = window.fetch.bind(window)
window.fetch = async (input, init) => {
	try {
		const res = await _originalFetch(input, init)
		if (res && (res.status === 401 || res.status === 403)) {
			try {
				// show toast to the user before redirecting
				toast.show('Sesión expirada o no autorizada. Redirigiendo al login...', 2000)
			} catch (e) {}
			try {
				auth.clearSession()
			} catch (e) {}
			// wait a bit to let the toast be visible
			await new Promise(r => setTimeout(r, 1200))
			try {
				if (router && router.push) {
					const current = router.currentRoute && router.currentRoute.value && router.currentRoute.value.path
					if (current !== '/') router.push('/')
				} else {
					window.location.href = '/'
				}
			} catch (e) {
				// ignore navigation errors
			}
		}
		return res
	} catch (err) {
		// network error - rethrow for callers to handle
		throw err
	}
}

createApp(App).use(router).mount('#app')
