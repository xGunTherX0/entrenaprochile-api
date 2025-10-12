# Frontend (Vue.js) — Instrucciones de despliegue en Netlify

Este README explica cómo apuntar tu frontend al backend desplegado en Render y desplegar en Netlify.

1. Asegúrate de que tu carpeta `frontend` contenga el proyecto Vue.js con `package.json`.

2. Crea (o edita) un archivo `.env.production` con la URL del backend:

```bash
# ejemplo: frontend/.env.production
VUE_APP_API_URL=https://entrenapro-backend.onrender.com
```

3. En tu código Vue, usa `process.env.VUE_APP_API_URL` para construir las llamadas a la API (Axios):

```js
// src/services/api.js (ejemplo)
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL
})

export default api
```

4. Subir el repo a Git y en Netlify usar:

- Base directory: `frontend`
- Build command: `npm run build`
- Publish directory: `dist`

Netlify hará builds automáticos al hacer push a la rama configurada.

*** Fin README
