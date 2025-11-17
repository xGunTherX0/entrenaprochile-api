# Despliegue automatizado: GitHub Actions + scripts locales

Este documento explica cómo desplegar el frontend en Netlify y el backend en Render sin poner claves en el repositorio.

Importante: NUNCA subas tus secretos (tokens/API keys) al repositorio. Usa GitHub Secrets y/o las interfaces de Netlify/Render.

Requisitos previos
- Tener el repositorio en GitHub (branch `master` que dispara los workflows).
- Tener acceso a las cuentas de Netlify y Render donde quieres publicar.

Secrets que debes configurar (GitHub repo -> Settings -> Secrets):
- `NETLIFY_AUTH_TOKEN` : token personal de Netlify (no lo pegues en el repo).
- `NETLIFY_SITE_ID` : el site id de Netlify (o `site` id de tu sitio).
- `VITE_API_BASE` (opcional): URL pública de tu backend (por ejemplo `https://mi-backend.onrender.com`).
- `RENDER_API_KEY` : API key de Render (hazlo en GitHub Secrets).
- `RENDER_SERVICE_ID` : el service id de tu servicio en Render.

Qué se añadió al repo
- `.github/workflows/deploy_frontend_netlify.yml` : workflow que construye el frontend (en `frontend`) y despliega con Netlify CLI usando `NETLIFY_AUTH_TOKEN` y `NETLIFY_SITE_ID`. Si defines `VITE_API_BASE` como secreto, el workflow lo escribe en `frontend/.env` antes de construir.
- `.github/workflows/deploy_backend_render.yml` : workflow que lanza un POST al endpoint de Render para crear un deploy usando `RENDER_API_KEY` y `RENDER_SERVICE_ID`.
- `scripts/deploy_netlify.ps1` : script PowerShell para ejecutar localmente (usa `NETLIFY_SITE_ID` y `NETLIFY_AUTH_TOKEN` en el entorno o parámetros).
- `scripts/deploy_render.ps1` : script PowerShell para ejecutar localmente y disparar un deploy en Render (usa `RENDER_SERVICE_ID` y `RENDER_API_KEY`).

Cómo usar (automatizado)
1. Ve a tu repo en GitHub -> Settings -> Secrets and variables -> Actions -> New repository secret. Añade los secretos listados arriba.
2. Push a la rama `master` para que ambos workflows se ejecuten automáticamente (el workflow de frontend construye y despliega; el de backend dispara un deploy en Render).
3. Verifica el progreso en Netlify y Render (dashboards). El workflow deja mensajes en la ejecución de Actions.

Cómo usar (manual, en tu máquina Windows PowerShell)
1. Abre PowerShell en la raíz del proyecto.
2. Exporta las variables en tu sesión (ejemplo):

```powershell
$env:NETLIFY_SITE_ID = "tu-site-id"
$env:NETLIFY_AUTH_TOKEN = "tu-netlify-token"
$env:RENDER_SERVICE_ID = "tu-render-service-id"
$env:RENDER_API_KEY = "tu-render-api-key"
```

3. Para desplegar frontend (local):

```powershell
.\scripts\deploy_netlify.ps1
```

4. Para disparar deploy del backend (local):

```powershell
.\scripts\deploy_render.ps1
```

Notas de seguridad
- No compartas los valores de tus secretos en chats públicos.
- Si alguna vez sospechas que un token fue expuesto, revócalo y crea uno nuevo.

Si quieres, puedo:
- Crear o ajustar los workflows para otra rama en lugar de `master`.
- Ayudarte a generar los valores `NETLIFY_SITE_ID` y `RENDER_SERVICE_ID` si me das instrucciones para obtenerlos desde tus dashboards (pero nunca pegues tokens aquí).
