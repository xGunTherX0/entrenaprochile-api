README - Despliegue (Render + Netlify)
=====================================

Este documento recoge pasos concretos para desplegar el backend en Render y el frontend en Netlify.

1) Backend - Render
---------------------
- Conecta este repo: `xGunTherX0/entrenaprochile-api` a Render y crea un nuevo *Web Service*.
- En *Environment* / *Build & Start commands* utiliza:
  - Build: `pip install -r backend/requirements.txt`
  - Start: `gunicorn backend.app:app --workers 2 --bind 0.0.0.0:$PORT`

- Variables de entorno (mínimas)
  - `DATABASE_URL` = postgres://... (tu BD de producción)
  - `ADMIN_EMAIL` = el email del admin (ej: `admin@test.local`)
  - `GOOGLE_CLIENT_ID` = Google client id usado por el backend para verificar tokens
  - `SECRET_KEY` o `JWT_SECRET` según tu configuración
  - `CORS_ORIGINS` opcional para restringir orígenes

- One-off: para crear el admin en la DB (ejecutar desde la consola de Render tras el primer deploy):
  ```bash
  python scripts/create_admin.py
  ```

2) Frontend - Netlify
----------------------
- Crea un nuevo site en Netlify y conéctalo al repo y rama que uses (ej. `master`).
- En *Build settings* indica:
  - Base directory: `frontend`
  - Build command: `npm run build`
  - Publish directory: `dist`

- Variables de entorno (Build env):
  - `VITE_GOOGLE_CLIENT_ID` = el client id para Google Identity (frontend)
  - `VITE_API_URL` = URL pública del backend (ej. `https://mi-backend.onrender.com`)
  - `VITE_ADMIN_EMAIL` = `admin@test.local` (opcional, UX)

3) Google Identity (producción)
--------------------------------
- En Google Cloud Console crea una credencial OAuth (Web application) o usa GSI.
- Añade en *Authorized JavaScript origins* el dominio de producción (ej. `https://mi-site.netlify.app`).
- Usa el mismo `client_id` en Netlify (`VITE_GOOGLE_CLIENT_ID`) y en Render (`GOOGLE_CLIENT_ID`).

4) Restringir cuentas Google (opcional)
--------------------------------------
- Si quieres permitir sólo cuentas de ciertos dominios, configura la variable de entorno `ALLOWED_GOOGLE_DOMAINS` en Render con una lista coma-separada (ej: `miempresa.com,otra.com`).
- El backend puede validar el dominio del email dentro del `google_signin` endpoint y devolver 403 si no está en la lista.

5) Qué comprobar después del deploy
-----------------------------------
- Backend: revisar logs en Render y health endpoint.
- Frontend: revisar Build logs en Netlify y probar el flujo de login con Google en producción.
- Ejecutar `scripts/create_admin.py` en producción y luego definir `ADMIN_EMAIL` en env vars.

Si quieres, puedo añadir la validación `ALLOWED_GOOGLE_DOMAINS` al backend y un `netlify.toml` de ejemplo (lo dejo en la rama).  
