# Backend (Flask) — Instrucciones de despliegue y creación de tablas

Este archivo explica cómo ejecutar el backend localmente, crear las tablas en la base de datos (local o en Render) y cómo desplegar en Render.

## Resumen

- El archivo principal es `backend/app.py`.
- La configuración de la base de datos usa la variable de entorno `DATABASE_URL`. Si no existe, la aplicación usa SQLite en `database/entrenapro.db`.
- Para crear las tablas hay dos utilidades:
  - `backend/manage.py` — CLI con comandos `create_tables` y `drop_tables`.
  - `backend/create_db.py` — script que, si no hay `DATABASE_URL` en el entorno, establece por defecto la URL de Render (solo para ejecuciones locales rápidas).

## Requisitos

- Python 3.8+ (el proyecto ya tiene un `venv` en `venv/` según tu configuración local)
- Instalar dependencias:

```powershell
C:/Users/carlo/U/EntrenaProChile/venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

## Ejecutar localmente (modo desarrollo)

1. Activa tu entorno virtual (PowerShell):

```powershell
C:/Users/carlo/U/EntrenaProChile/venv/Scripts/Activate.ps1
```

2. Instala dependencias (si no lo hiciste):

```powershell
python -m pip install -r backend/requirements.txt
```

3. (Opcional) Si quieres usar la base de Render desde tu PC, ahora `backend/create_db.py` **no** contiene una URL por defecto. Puedes:

- Pasar la URL por argumento CLI:

```powershell
C:/Users/carlo/U/EntrenaProChile/venv/Scripts/python.exe backend/create_db.py --database-url "postgresql://USER:PASS@HOST/DATABASE"
```

- O exportar la variable de entorno y usar `manage.py`:

```powershell
# Exportar la URL (Windows PowerShell)
$env:DATABASE_URL = 'postgresql://USER:PASS@HOST/DATABASE'

# Crear tablas usando manage.py
C:/Users/carlo/U/EntrenaProChile/venv/Scripts/python.exe backend/manage.py create_tables
```

Nota: `create_db.py` ahora prefiere el argumento `--database-url` y, si no se pasa, usa la variable de entorno `DATABASE_URL`. Esto evita mantener credenciales en el código.

## Desplegar en Render (pasos recomendados)

1. Entra a Render y crea un nuevo **Web Service** vinculando tu repositorio.

2. Configura **Build Command** y **Start Command** como sigue (Render ejecuta en un entorno Linux; usa la ruta al requirements en `backend/`):

- Build Command:

```bash
pip install -r backend/requirements.txt
```

- Start Command:

```bash
gunicorn backend.app:app --bind 0.0.0.0:$PORT
```

3. Conecta o crea una base de datos PostgreSQL en Render y **setea** la variable de entorno `DATABASE_URL` (Render la suministra automáticamente si conectas una DB gestionada).

4. Crear las tablas en Render (opciones):

- Opción A — desde la interfaz de Render: crea un **one-off job** y ejecuta:

```bash
python backend/manage.py create_tables
```

  Render correrá ese comando donde `DATABASE_URL` ya está definido y creará las tablas en la base de datos asociada.

- Opción B — si ejecutas desde tu máquina local y `DATABASE_URL` apunta a la DB de Render, usa `backend/create_db.py` (ya incluido) o exporta la variable y usa `manage.py`.

## Seguridad y buenas prácticas

- Evita mantener credenciales en código. `backend/create_db.py` actualmente incluye la URL proporcionada para conveniencia local; te recomiendo eliminarla o comentarla una vez hayas creado las tablas, o usar en su lugar `os.environ['DATABASE_URL']` desde tu terminal.
- No subas archivos con secretos al repositorio.

## Troubleshooting

- Si `gunicorn` no encuentra `backend.app:app`, verifica que el módulo sea importable (desde la raíz del repo `import backend` debe funcionar).
- Si `db.create_all()` no crea tablas, asegúrate de que tus modelos estén importados antes de llamar a `create_all()` (Flask-SQLAlchemy solo registra modelos que han sido importados en el proceso actual).

## Próximos pasos sugeridos

- (Opcional) Eliminar la URL incrustada en `backend/create_db.py` y usar solo variables de entorno.
- Añadir migraciones con Alembic/Flask-Migrate para gestionar cambios de esquema en producción.
