Local - Cómo ejecutar el proyecto EntrenaProChile

Objetivo
- Hacer que la app funcione en tu máquina local (backend Flask + frontend Vite) para poder probar cambios y evitar múltiples deploys.

Requisitos previos
- Windows (PowerShell disponible)
- Python 3.10+ (preferible en un virtualenv)
- Node.js 16+ y npm

Pasos rápidos (resumen)
1) Crear/activar venv e instalar dependencias Python
2) Instalar dependencias frontend (npm install)
3) Iniciar backend
4) Iniciar frontend (dev) — proxy a /api configurado
5) Ejecutar pruebas rápidas

Comandos detallados (PowerShell)
# En la raíz del repo
cd C:\Users\carlo\U\EntrenaProChile

# 1) Python (crea y activa virtualenv si no lo tienes)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

# 2) Frontend deps
cd frontend
npm install
# Vite dev server usará la variable VITE_API_BASE si la tienes en frontend/.env
# Asegúrate de que frontend/.env contiene:
# VITE_API_BASE=http://localhost:5000

# 3) Inicia backend (en otra terminal)
cd C:\Users\carlo\U\EntrenaProChile
.\.venv\Scripts\Activate.ps1
# Opcional: exporta variables que quieras (ADMIN_EMAIL, ADMIN_PASSWORD, DEV_PROMOTE_SECRET)
$env:ADMIN_EMAIL='admin@test.local'; $env:ADMIN_PASSWORD='admin123'
# Si quieres probar con CORS explícito (por ejemplo para usar frontend en otro host) define:
# $env:CORS_ORIGINS='http://localhost:5173,https://mi-frontend.com'
& .\.venv\Scripts\python.exe -m backend.app

# 4) Inicia frontend (otra terminal)
cd C:\Users\carlo\U\EntrenaProChile\frontend
npm run dev
# Abre: http://localhost:5173

# 5) Ejecutar pruebas (opcional)
# Ejecutar desde la raíz del repo; asegurarse que PYTHONPATH está apuntando al repo
$env:PYTHONPATH='C:\Users\carlo\U\EntrenaProChile'; & 'C:\Users\carlo\U\EntrenaProChile\.venv\Scripts\python.exe' -m pytest -q

Configuraciones importantes
- CORS_ORIGINS: ahora el backend admite '*' o lista (comma o JSON array). Para aceptar cookies/authorization con credenciales, no uses '*', define orígenes explícitos. Ejemplo:
  CORS_ORIGINS=http://localhost:5173,https://entrenaprochile-frontend.netlify.app

- VITE_API_BASE: define en `frontend/.env` para apuntar al backend. En desarrollo dejamos:
  VITE_API_BASE=http://localhost:5000

Notas para deploy (Render u otro)
- En Render/Heroku/Netlify (según sea backend/frontend): configura variables de entorno:
  - DATABASE_URL (Postgres en producción)
  - ADMIN_EMAIL, ADMIN_PASSWORD
  - CORS_ORIGINS (comma-separated list con tu dominio de frontend y opcionalmente http://localhost:5173 para pruebas locales)
- Redeploy del servicio backend para que recoja `CORS_ORIGINS`.

Limpieza antes de producción
- El código contiene reparaciones "defensivas" (ALTER/CREATE IF NOT EXISTS) diseñadas para development; revisa y elimina o condiciona estos bloques si quieres un deployment más limpio.

Si quieres que haga el siguiente paso ahora:
- Puedo ejecutar `npm run build` en `frontend` y verificar que `vite preview` sirve el build correctamente.
- Puedo preparar el texto exacto para configurar Render (valores de CORS_ORIGINS y pasos) y dejarlo listo para pegar.

Si me das permiso explícito para crear/editar archivos de deploy (por ejemplo `render.yaml` o ajustes de prod), lo hago ahora.
