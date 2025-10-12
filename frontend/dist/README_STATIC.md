EntrenaProChile - Frontend estático de prueba

Archivos en esta carpeta son un frontend mínimo para permitir que Netlify publique un sitio estático y pruebe las llamadas al backend.

Cómo funciona:
- `index.html` – formulario simple de login.
- `main.js` – envía POST a `https://entrenaprochile-api.onrender.com/api/usuarios/login` y muestra la respuesta.

Si usas Netlify conectado a este repo, confirma que la "Publish directory" está configurada como `frontend/dist` o cambia a `dist` según tu configuración.
