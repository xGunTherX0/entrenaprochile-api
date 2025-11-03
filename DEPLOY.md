## Variables de entorno y despliegue (Render)

Antes de desplegar en Render asegúrate de definir las siguientes variables de entorno en el servicio (Dashboard → tu Service → Environment / Environment Variables):

- `DATABASE_URL` — URL de la base de datos PostgreSQL en producción.
- `JWT_SECRET` — secreto fuerte para firmar JWT. Genera uno localmente con `openssl rand -hex 32` o con PowerShell (ver abajo).
- `JWT_EXPIRES_SECONDS` — tiempo en segundos para que expire el token JWT (ej. `3600`).
- `CORS_ORIGINS` — dominio(s) permitidos para CORS, p.ej. `https://tu-frontend.netlify.app`. Por defecto el servidor permite `*` si no se define.
- `DEV_PROMOTE_SECRET` — (opcional) secreto para habilitar temporalmente el endpoint de promoción a entrenador en pruebas. Elimínalo cuando termines.

Cómo generar un `JWT_SECRET` en PowerShell (Windows):
```powershell
$bytes = New-Object Byte[] 32
(New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($bytes)
[System.BitConverter]::ToString($bytes) -replace '-',''
```

Después de añadir/actualizar variables en Render, fuerza un redeploy (Manual Deploy o Restart) para que el servicio lea las nuevas variables.

## Pruebas E2E locales (script)
He incluido un script útil en `scripts/e2e.js` que automatiza: login → registro opcional → (promote opcional) → crear medición → crear rutina → listar → borrar rutina.

Requisitos: Node 18+ (soporta fetch nativo).

Uso rápido (desde la carpeta del repo):
```bash
# Opcional: exporta variables si tu API no es la pública por defecto
# export API_URL='https://entrenaprochile-api.onrender.com'
# export DEV_PROMOTE_SECRET='promote-abc-123'
node scripts/e2e.js
```

El script imprime un JSON con el resultado de cada paso. No compartas aquí el token completo (el script lo redacta en la salida).

## Notas de seguridad
- No expongas `JWT_SECRET` ni `DATABASE_URL` con credenciales en el repo o en chats.
- Elimina `DEV_PROMOTE_SECRET` y el endpoint dev cuando termines las pruebas en producción.
