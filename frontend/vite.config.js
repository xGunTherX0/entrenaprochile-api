import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
  ,
  // Dev proxy: redirige llamadas a /api al backend objetivo para evitar CORS en desarrollo.
  // Usa la variable de entorno VITE_API_BASE si está definida, o http://localhost:5000 por defecto.
  server: {
    // Allow dev server to set helpful headers so Google Identity iframe
    // can communicate via postMessage during local development.
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin-allow-popups'
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE || 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        // rewrite no es necesario si la ruta /api coincide exactamente, pero lo dejamos explícito
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  }
})
