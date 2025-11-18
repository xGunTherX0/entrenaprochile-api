# This is a Python file for the Flask application.
# It contains various endpoints for user management and routines.
# Ensure to configure the environment variables before running.
import os
from flask import Flask, jsonify, request
from datetime import datetime
# Mejor configuración CORS: permitimos los encabezados comunes (Authorization, Content-Type)
# y soportamos credenciales si es necesario. `CORS_ORIGINS` puede venir desde entorno.
from flask_cors import CORS
# Asumiendo que usas Flask-SQLAlchemy para el ORM

# Inicialización de la aplicación
app = Flask(__name__)

# Global JSON error handler: return JSON for unhandled exceptions so the frontend
# receives a machine-readable error (detailed in development, generic in prod).
@app.errorhandler(Exception)
def handle_exception(e):
    # Global handler: don't leak internals in production, but show details in dev
    is_prod = bool(os.getenv('DATABASE_URL'))
    app.logger.exception('Unhandled exception')
    if is_prod:
        return jsonify({'error': 'internal server error'}), 500
    else:
        # In development return the exception string for easier debugging.
        # Also persist the traceback and request payload to a logfile to help
        # debugging when the server console isn't available.
        try:
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            with open(os.path.join(logs_dir, 'global_exception.log'), 'a', encoding='utf-8') as fh:
                fh.write('----\n')
                fh.write(f'TIME: {datetime.utcnow().isoformat()}\n')
                fh.write(f'PATH: {getattr(request, "path", None)}\n')
                fh.write('TRACEBACK:\n')
                import traceback as _tb
                fh.write(_tb.format_exc())
                fh.write('\nREQUEST_BODY:\n')
                try:
                    fh.write(repr(request.get_json() if request.is_json else request.data) + '\n')
                except Exception:
                    pass
        except Exception:
            # best-effort: don't raise from logging
                pass
        return jsonify({'error': 'internal', 'detail': str(e)}), 500

# Configurable CORS: limita orígenes en producción usando la variable de entorno
# `CORS_ORIGINS`. Por defecto permite todos ('*') para facilitar pruebas.
import os as _os
# Default to localhost Vite dev origin when not provided to help local development.
# In production set the env var `CORS_ORIGINS` to your frontend origin(s).
_cors_origins = _os.getenv('CORS_ORIGINS', 'http://localhost:5173')

# Configure CORS explicitly so preflight (OPTIONS) respuestas incluyan los encabezados necesarios.
# Support flexible values in CORS_ORIGINS:
# - '*' (default) -> allow all origins, but we do NOT enable credentials for '*'
# - comma-separated list (e.g. 'http://localhost:5173,https://example.com') -> enable credentials
# - JSON array string (e.g. '["http://a","http://b"]') -> enable credentials
app.config.setdefault('CORS_HEADERS', 'Content-Type,Authorization')

def _parse_cors_origins(value):
    v = (value or '').strip()
    # allow '*' or empty -> wildcard
    if v == '*' or v == '':
        return '*', False
    # try JSON list first
    try:
        import json
        if v.startswith('['):
            arr = json.loads(v)
            origins = [s for s in (arr or []) if isinstance(s, str) and s.strip()]
            if origins:
                return origins, True
    except Exception:
        pass
    # fallback: comma-separated
    origins = [s.strip() for s in v.split(',') if s.strip()]
    if not origins:
        return '*', False
    return origins, True

cors_origins_config, cors_supports_credentials = _parse_cors_origins(_cors_origins)
app.logger.debug('CORS origins resolved: %s supports_credentials=%s', cors_origins_config, cors_supports_credentials)

CORS(app,
    resources={r"/api/*": {"origins": cors_origins_config}},
    supports_credentials=cors_supports_credentials,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])


# Ensure OPTIONS preflight requests to our API return 200 before auth decorators run.
# Some auth decorators may be applied to routes and could reject OPTIONS (no Authorization header),
# which causes the browser preflight to fail. Return a simple 200 for API OPTIONS so flask-cors
# can attach the proper CORS headers and the real request can proceed.
@app.before_request
def _handle_api_options_preflight():
    try:
        if request.method == 'OPTIONS' and request.path.startswith('/api/'):
            return ('', 200)
    except Exception:
        # In case request isn't available or other unexpected error, don't block startup
        pass


# Ensure CORS headers are present on all /api/* responses (robust fallback)
@app.after_request
def _ensure_cors_headers(response):
    try:
        # Only modify API responses
        if request.path and request.path.startswith('/api/'):
            origin = request.headers.get('Origin')
            # Determine allowed origin value
            allowed = cors_origins_config
            if allowed == '*':
                response.headers.setdefault('Access-Control-Allow-Origin', '*')
            else:
                # allowed may be a list
                try:
                    if isinstance(allowed, (list, tuple)):
                        if origin and origin in allowed:
                            response.headers.setdefault('Access-Control-Allow-Origin', origin)
                        else:
                            # fallback to first configured origin
                            response.headers.setdefault('Access-Control-Allow-Origin', allowed[0] if allowed else '')
                    else:
                        response.headers.setdefault('Access-Control-Allow-Origin', str(allowed))
                except Exception:
                    response.headers.setdefault('Access-Control-Allow-Origin', '*')

            # Credentials
            if cors_supports_credentials:
                response.headers.setdefault('Access-Control-Allow-Credentials', 'true')

            # Allowed methods and headers
            response.headers.setdefault('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            response.headers.setdefault('Access-Control-Allow-Headers', app.config.get('CORS_HEADERS', 'Content-Type,Authorization'))
    except Exception:
        pass
    return response

from werkzeug.security import generate_password_hash, check_password_hash
from backend.auth import generate_token
from sqlalchemy import text
import traceback


@app.route('/api/usuarios/register', methods=['POST'])
def register_usuario():
    data = request.get_json() or {}
    email = data.get('email')
    nombre = data.get('nombre') or data.get('name') or 'Usuario'
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400

    # Verifica si existe
    existing = Usuario.query.filter_by(email=email).first()
    if existing:
        return jsonify({'error': 'user exists'}), 409

    hashed = generate_password_hash(password)
    user = Usuario(email=email, nombre=nombre, hashed_password=hashed)
    db.session.add(user)
    db.session.commit()

    # Crear entidad Cliente por defecto
    cliente = Cliente(usuario_id=user.id)
    db.session.add(cliente)
    db.session.commit()

    return jsonify({'message': 'user created', 'id': user.id}), 201


@app.route('/api/usuarios/login', methods=['POST'])
def login_usuario():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400

    user = Usuario.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'invalid credentials'}), 401

    # Check lockout state
    try:
        from datetime import datetime as _dt
        if getattr(user, 'locked_until', None) and user.locked_until > _dt.utcnow():
            return jsonify({'error': 'account locked', 'locked_until': user.locked_until.isoformat()}), 403
    except Exception:
        pass

    if not check_password_hash(user.hashed_password, password):
        # increment failed attempts and possibly lock account
        try:
            user.failed_attempts = (getattr(user, 'failed_attempts', 0) or 0) + 1
            # lock after 3 failed attempts
            if user.failed_attempts >= 3:
                from datetime import datetime as _dt, timedelta as _td
                lock_minutes = int(os.getenv('ACCOUNT_LOCK_MINUTES', '15'))
                user.locked_until = _dt.utcnow() + _td(minutes=lock_minutes)
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return jsonify({'error': 'invalid credentials'}), 401

    # Determina rol según relaciones (Cliente / Entrenador)
    # Prioridad: si el usuario es el ADMIN (según variable de entorno)
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@test.local')
    if user.email == ADMIN_EMAIL:
        role = 'admin'
    else:
        role = 'usuario'
        if getattr(user, 'entrenador', None):
            role = 'entrenador'
        elif getattr(user, 'cliente', None):
            role = 'cliente'

    # Reset failed attempts on successful login
    try:
        user.failed_attempts = 0
        user.locked_until = None
        db.session.add(user)
        db.session.commit()
    except Exception:
        db.session.rollback()

    # Generar token JWT con user info (incluye jti desde backend.auth)
    token = generate_token({'user_id': user.id, 'role': role, 'nombre': user.nombre})
    # Devuelve role, nombre y token
    return jsonify({'message': 'ok', 'user_id': user.id, 'role': role, 'nombre': user.nombre, 'token': token}), 200


# --- Lógica de Conexión (el cambio clave) ---

# 1. Obtiene la URL de la base de datos de la variable de entorno 'DATABASE_URL'
#    Render establecerá automáticamente esta variable cuando despliegues.
DATABASE_URL = os.getenv('DATABASE_URL')

# 2. Adapta la URL si es necesario y define la conexión final
if DATABASE_URL:
    # Render a veces usa 'postgres://', pero SQLAlchemy requiere 'postgresql://'
    # Esta línea asegura que el formato sea el correcto para el despliegue
    SQLALCHEMY_URI = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("Modo Producción: Conectando a PostgreSQL")

    # Ensure SSL mode for Postgres connections on platforms that require it
    # (Render-managed Postgres often requires SSL). If the connection string
    # doesn't already include sslmode, append it. This is safe because if
    # the param is already present we don't modify the URI.
    if SQLALCHEMY_URI.startswith('postgresql://') and 'sslmode=' not in SQLALCHEMY_URI:
        if '?' in SQLALCHEMY_URI:
            SQLALCHEMY_URI = SQLALCHEMY_URI + '&sslmode=require'
        else:
            SQLALCHEMY_URI = SQLALCHEMY_URI + '?sslmode=require'
else:
    # Si no se encuentra la variable (estás en tu PC), usa SQLite (Modo Desarrollo)
    # Construimos una ruta absoluta al archivo dentro del repo para evitar
    # problemas dependientes del directorio de trabajo.
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_file = os.path.join(repo_root, 'database', 'entrenapro.db')
    # SQLite URIs en Windows necesitan / separadores, y triple slash para ruta absoluta
    SQLALCHEMY_URI = f"sqlite:///{db_file.replace('\\', '/')}"
    print(f"Modo Desarrollo: Conectando a SQLite ({SQLALCHEMY_URI})")

# 3. Asigna la URI a la configuración de la aplicación
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_URI

# Opcional pero recomendado para producción:
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from database.database import db as db_instance

# Inicializa tu ORM (instancia compartida)
db_instance.init_app(app)
# Para compatibilidad con el resto del código, exportamos `db`
db = db_instance

# Importa modelos después de inicializar db para evitar importación circular
with app.app_context():
    from database.database import Usuario, Cliente, Entrenador, Medicion  # noqa: F401
    from database.database import Rutina  # noqa: F401
    from backend.auth import jwt_required

    # --- Seed: crear usuario administrador por defecto si no existe ---
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@test.local')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    try:
        admin_exists = Usuario.query.filter_by(email=ADMIN_EMAIL).first()
        if not admin_exists:
            hashed = generate_password_hash(ADMIN_PASSWORD)
            admin_user = Usuario(email=ADMIN_EMAIL, nombre='Administrador', hashed_password=hashed)
            db.session.add(admin_user)
            db.session.commit()
            # Crear filas Cliente y Entrenador para el admin por conveniencia en pruebas
            try:
                cliente = Cliente(usuario_id=admin_user.id)
                db.session.add(cliente)
                entrenador = Entrenador(usuario_id=admin_user.id)
                db.session.add(entrenador)
                db.session.commit()
            except Exception:
                # no fatal, seguimos
                db.session.rollback()
            print(f"Admin creado: {ADMIN_EMAIL} (cliente+entrenador creados)")
    except Exception:
        # Si la base de datos aún no está migrada o hay un error, no interrumpimos el arranque
        pass

# CREAR TABLAS AUTOMÁTICAMENTE EN DESARROLLO (NO EJECUTAR EN PRODUCCIÓN)
if not DATABASE_URL:
    try:
        with app.app_context():
            db.create_all()
            print('DB: create_all executed (development mode)')
            # Ensure development-only columns that might be missing are added.
            # Some older dev DBs may lack the `activo` column on usuarios which
            # causes OperationalError when admin endpoints try to read it.
            try:
                # SQLite supports simple ADD COLUMN; wrap in try/except to ignore
                # if the column already exists. This is safe in development only.
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN activo BOOLEAN DEFAULT 1"))
                db.session.commit()
            except Exception:
                # ignore failures (e.g., column exists or DB doesn't support ALTER)
                db.session.rollback()
            # Also attempt to add entrenador profile columns in dev
                try:
                    # bio and telefono are optional; attempt to add if missing
                    db.session.execute(text("ALTER TABLE entrenadores ADD COLUMN bio TEXT"))
                    db.session.execute(text("ALTER TABLE entrenadores ADD COLUMN telefono VARCHAR(50)"))
                    # instagram_url and youtube_url for trainer profile
                    try:
                        db.session.execute(text("ALTER TABLE entrenadores ADD COLUMN instagram_url VARCHAR(255)"))
                    except Exception:
                        db.session.rollback()
                    try:
                        db.session.execute(text("ALTER TABLE entrenadores ADD COLUMN youtube_url VARCHAR(255)"))
                    except Exception:
                        db.session.rollback()
                    db.session.commit()
                except Exception:
                    # ignore failures; these ALTERs are best-effort in dev
                    db.session.rollback()

            # Ensure new development columns/tables for security features
            try:
                # add failed_attempts and locked_until if missing
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN failed_attempts INTEGER DEFAULT 0"))
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN locked_until TIMESTAMP"))
                # create revoked_tokens table if not exists (SQLite/Postgres compatible)
                db.session.execute(text("CREATE TABLE IF NOT EXISTS revoked_tokens (id INTEGER PRIMARY KEY AUTOINCREMENT, jti VARCHAR(128) UNIQUE NOT NULL, revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
                db.session.commit()
            except Exception:
                db.session.rollback()
            # Attempt to add new rutina description section columns in development DBs
            try:
                db.session.execute(text("ALTER TABLE rutinas ADD COLUMN objetivo_principal TEXT"))
                db.session.execute(text("ALTER TABLE rutinas ADD COLUMN enfoque_rutina TEXT"))
                db.session.execute(text("ALTER TABLE rutinas ADD COLUMN cualidades_clave TEXT"))
                db.session.execute(text("ALTER TABLE rutinas ADD COLUMN duracion_frecuencia TEXT"))
                db.session.execute(text("ALTER TABLE rutinas ADD COLUMN material_requerido TEXT"))
                db.session.execute(text("ALTER TABLE rutinas ADD COLUMN instrucciones_estructurales TEXT"))
                db.session.commit()
            except Exception:
                db.session.rollback()
    except Exception as e:
        print('DB create_all failed:', e)


# Asegura que la carpeta database exista cuando uses SQLite en desarrollo
if not DATABASE_URL:
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
    try:
        os.makedirs(db_dir, exist_ok=True)
    except Exception:
        # No fatal, solo intentamos crear el directorio
        pass


# --- Reparaciones ligeras de esquema en producción ---
# Algunos despliegues (p. ej. al restaurar una DB antigua) pueden carecer de
# columnas que el código asume presentes. Hacemos un intento seguro y no fatal
# de añadir las columnas mínimas usadas en tiempo de ejecución para evitar
# errores como `column usuarios.activo does not exist`.
if DATABASE_URL:
    try:
        with app.app_context():
            try:
                # Añadir columnas si faltan (Postgres soporta IF NOT EXISTS)
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT true"))
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS failed_attempts INTEGER DEFAULT 0"))
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP"))
                # Tabla para tokens revocados (si no existe)
                # Use SERIAL para compatibilidad con Postgres; SQLite ignorará SERIAL
                try:
                    db.session.execute(text("CREATE TABLE IF NOT EXISTS revoked_tokens (id SERIAL PRIMARY KEY, jti VARCHAR(128) UNIQUE NOT NULL, revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
                except Exception:
                    # Fallback: portable create without SERIAL (use integer PK)
                    try:
                        db.session.execute(text("CREATE TABLE IF NOT EXISTS revoked_tokens (id INTEGER PRIMARY KEY, jti VARCHAR(128) UNIQUE NOT NULL, revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
                    except Exception:
                        pass
                db.session.commit()
            except Exception:
                db.session.rollback()
    except Exception:
        # No bloquear el arranque por fallos en estas reparaciones; dejamos que
        # el app.logger capture detalles en los logs de Render.
        app.logger.exception('production schema repair failed')


# Ruta de prueba rápida
@app.route('/ping')
def ping():
    return jsonify({'status': 'ok'})


@app.route('/', methods=['GET'])
def root_health():
    """Health check for Render / external load balancers. Returns 200 OK.
    This helps detect whether Flask is running and responding at the root path.
    """
    return jsonify({'status': 'ok'}), 200


@app.route('/api', methods=['GET'])
def api_root():
    """Simple API root to confirm that /api routes are reachable.
    This is temporary and helps confirm whether the Flask app is mounting
    the API under the expected path on Render.
    """
    return jsonify({'api': 'ok'}), 200


@app.route('/api/mediciones', methods=['POST'])
@jwt_required
def crear_medicion():
    data = request.get_json() or {}
    peso = data.get('peso')
    altura = data.get('altura')
    cintura = data.get('cintura')

    # Obtener cliente por el user_id incluido en el token
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    cliente = Cliente.query.filter_by(usuario_id=token_user_id).first()
    if not cliente:
        return jsonify({'error': 'cliente not found'}), 404

    try:
        medicion = Medicion(cliente_id=cliente.id, peso=peso, altura=altura, cintura=cintura)
        db.session.add(medicion)
        db.session.commit()
        return jsonify({'message': 'medicion creada', 'id': medicion.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/mediciones/<int:cliente_id>', methods=['GET'])
@jwt_required
def listar_mediciones(cliente_id):
    # Ensure the token user matches the requested cliente_id's usuario
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    cliente = Cliente.query.filter_by(id=cliente_id).first()
    if not cliente:
        return jsonify({'error': 'cliente not found'}), 404

    # verify ownership: the cliente.usuario_id must match token user
    if cliente.usuario_id != token_user_id:
        return jsonify({'error': 'forbidden: cannot view mediciones of another cliente'}), 403

    mediciones = Medicion.query.filter_by(cliente_id=cliente.id).order_by(Medicion.creado_en.desc()).all()
    result = []
    for m in mediciones:
        result.append({'id': m.id, 'peso': m.peso, 'altura': m.altura, 'cintura': m.cintura, 'creado_en': m.creado_en.isoformat()})
    return jsonify(result), 200


@app.route('/api/rutinas', methods=['POST'])
@jwt_required
def crear_rutina():
    data = request.get_json() or {}
    # Log incoming payload for debugging (also persist to file to help users without console access)
    try:
        app.logger.debug('crear_rutina payload: %s', data)
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        with open(os.path.join(logs_dir, 'crear_rutina_payload.log'), 'a', encoding='utf-8') as fh:
            fh.write(f"----\nTIME: {datetime.utcnow().isoformat()}\nPAYLOAD: {repr(data)}\n")
    except Exception:
        # best-effort logging; don't fail the request because of logging
        pass
    entrenador_usuario_id = data.get('entrenador_id') or data.get('user_id')
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    # Support detailed sections instead of a single select
    seccion_descripcion = data.get('seccion_descripcion')
    link_url = data.get('link_url')
    objetivo_principal = data.get('objetivo_principal')
    enfoque_rutina = data.get('enfoque_rutina')
    cualidades_clave = data.get('cualidades_clave')
    duracion_frecuencia = data.get('duracion_frecuencia')
    material_requerido = data.get('material_requerido')
    instrucciones_estructurales = data.get('instrucciones_estructurales')
    nivel = data.get('nivel')
    # Always keep new rutinas not-public by default; admin must approve to publish.
    # Ignore any client-supplied `es_publica` to enforce review workflow.
    es_publica = False

    header_user_id = request.jwt_payload.get('user_id')

    # If the client provided an entrenador_usuario_id in body ensure it matches the token user
    if entrenador_usuario_id:
        try:
            entrenador_usuario_id = int(entrenador_usuario_id)
        except Exception:
            return jsonify({'error': 'invalid entrenador_id'}), 400
        if entrenador_usuario_id != header_user_id:
            return jsonify({'error': 'forbidden: cannot create rutina for another entrenador'}), 403

    # Buscar entrenador por el usuario autenticado (from token)
    entrenador = Entrenador.query.filter_by(usuario_id=header_user_id).first()
    if not entrenador:
        return jsonify({'error': 'entrenador not found or not authenticated as entrenador'}), 404

    if not nombre:
        return jsonify({'error': 'nombre required'}), 400

    rutina = Rutina(
        entrenador_id=entrenador.id,
        nombre=nombre,
        descripcion=descripcion,
        link_url=link_url,
        seccion_descripcion=seccion_descripcion,
        objetivo_principal=objetivo_principal,
        enfoque_rutina=enfoque_rutina,
        cualidades_clave=cualidades_clave,
        duracion_frecuencia=duracion_frecuencia,
        material_requerido=material_requerido,
        instrucciones_estructurales=instrucciones_estructurales,
        nivel=nivel,
        es_publica=es_publica
    )
    db.session.add(rutina)
    try:
        # Flush to assign rutina.id without committing yet
        try:
            db.session.flush()
        except Exception:
            # If flush fails, attempt to create tables and retry once
            try:
                with app.app_context():
                    db.create_all()
                db.session.flush()
            except Exception:
                db.session.rollback()
                app.logger.exception('crear_rutina: flush failed')
                return jsonify({'error': 'db error', 'detail': 'flush failed'}), 500

        # Attempt to create ContentReview in a nested transaction (savepoint).
        review_created = False
        try:
            from database.database import ContentReview
            existing = None
            try:
                existing = ContentReview.query.filter_by(tipo='rutina', content_id=rutina.id).first()
            except Exception:
                existing = None

            # If no existing review row, attempt to create one in a nested transaction
            if not existing:
                try:
                    with db.session.begin_nested():
                        review = ContentReview(tipo='rutina', content_id=rutina.id, estado='pendiente', creado_por=header_user_id)
                        db.session.add(review)
                    # nested commit succeeded
                    review_created = True
                except Exception:
                    # nested failed — log and continue, we'll commit rutina below
                    try:
                        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
                        os.makedirs(logs_dir, exist_ok=True)
                        with open(os.path.join(logs_dir, 'crear_rutina_review_error.log'), 'a', encoding='utf-8') as fh:
                            fh.write('----\n')
                            fh.write(f'TIME: {datetime.utcnow().isoformat()}\n')
                            fh.write(f'RUTINA_ID: {getattr(rutina, "id", None)}\n')
                            fh.write(f'CREADO_POR: {header_user_id}\n')
                            import traceback as _tb
                            fh.write('TRACEBACK:\n')
                            fh.write(_tb.format_exc())
                            fh.write('\n')
                    except Exception:
                        pass
        except Exception:
            # importing ContentReview or querying failed — log and proceed
            app.logger.exception('crear_rutina: ContentReview check failed')

        # Now commit the session (this will persist rutina and any nested changes that succeeded)
        try:
            db.session.commit()
        except Exception as e:
            # If commit fails, rollback and attempt to persist rutina alone
            app.logger.exception('crear_rutina: commit failed, attempting resilient save')
            try:
                db.session.rollback()
            except Exception:
                pass
            # Fallback: try to save rutina in a new session scope
            try:
                with app.app_context():
                    db.session.add(rutina)
                    db.session.commit()
            except Exception:
                db.session.rollback()
                app.logger.exception('crear_rutina: final commit failed')
                try:
                    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
                    os.makedirs(logs_dir, exist_ok=True)
                    with open(os.path.join(logs_dir, 'crear_rutina_error.log'), 'a', encoding='utf-8') as fh:
                        fh.write('----\n')
                        fh.write(f'TIME: {datetime.utcnow().isoformat()}\n')
                        fh.write('TRACEBACK:\n')
                        fh.write(traceback.format_exc())
                        fh.write('\nPAYLOAD:\n')
                        try:
                            fh.write(repr(data) + '\n')
                        except Exception:
                            pass
                except Exception:
                    pass
                return jsonify({'error': 'db error', 'detail': str(e)}), 500

        # Return success payload after creating rutina
        return jsonify({'message': 'rutina creada', 'rutina': {'id': rutina.id, 'nombre': rutina.nombre, 'descripcion': rutina.descripcion, 'link_url': getattr(rutina, 'link_url', None), 'objetivo_principal': rutina.objetivo_principal, 'enfoque_rutina': rutina.enfoque_rutina, 'cualidades_clave': rutina.cualidades_clave, 'duracion_frecuencia': rutina.duracion_frecuencia, 'material_requerido': rutina.material_requerido, 'instrucciones_estructurales': rutina.instrucciones_estructurales, 'nivel': rutina.nivel, 'es_publica': rutina.es_publica, 'creado_en': rutina.creado_en.isoformat()}}), 201
    except Exception as e:
        # Immediate, clear diagnostic in development: return traceback so frontend shows reason
        app.logger.exception('crear_rutina: immediate failure')
        db.session.rollback()
        # try to persist the traceback for offline inspection
        try:
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            with open(os.path.join(logs_dir, 'crear_rutina_error.log'), 'a', encoding='utf-8') as fh:
                fh.write('----\n')
                fh.write(f'TIME: {datetime.utcnow().isoformat()}\n')
                fh.write('TRACEBACK:\n')
                fh.write(traceback.format_exc())
                fh.write('\nPAYLOAD:\n')
                try:
                    fh.write(repr(data) + '\n')
                except Exception:
                    pass
        except Exception:
            pass
        # Return the formatted traceback to the client in development for quick diagnosis
        return jsonify({'error': 'db error', 'detail': traceback.format_exc()}), 500


@app.route('/api/rutinas/<int:entrenador_usuario_id>', methods=['GET'])
@jwt_required
def listar_rutinas(entrenador_usuario_id):
    # Wrap the entire handler in a broad try/except to ensure any unexpected
    # error returns JSON (helpful during development) and is logged.
    try:
        header_user_id = request.jwt_payload.get('user_id')
        if header_user_id != entrenador_usuario_id:
            return jsonify({'error': 'forbidden: cannot view rutinas of another entrenador'}), 403

        entrenador = Entrenador.query.filter_by(usuario_id=entrenador_usuario_id).first()
        if not entrenador:
            return jsonify({'error': 'entrenador not found'}), 404

        # Ejecutar la consulta de forma resiliente: si faltan columnas en la tabla
        # (problema observado en despliegues), intentamos reparar el esquema y reintentar.
        try:
            rutinas = Rutina.query.filter_by(entrenador_id=entrenador.id).order_by(Rutina.creado_en.desc()).all()
        except Exception as e:
            err_str = str(e)
            app.logger.exception('listar_rutinas: query failed, attempting repair')
            # Intentar reparaciones simples cuando la excepción sugiere columna faltante
            if 'UndefinedColumn' in err_str or ('column' in err_str and 'does not exist' in err_str) or 'no such column' in err_str:
                try:
                    with app.app_context():
                        db.create_all()
                        expected_cols = {
                            'entrenador_id': 'INTEGER',
                            'nombre': 'VARCHAR(200)',
                            'descripcion': 'TEXT',
                            'nivel': 'VARCHAR(50)',
                            'es_publica': 'BOOLEAN',
                            'creado_en': 'TIMESTAMP'
                        }
                        for c, ttype in expected_cols.items():
                            try:
                                db.session.execute(text(f"ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS {c} {ttype}"))
                            except Exception:
                                pass
                        try:
                            has = db.session.execute(text("SELECT conname FROM pg_constraint WHERE conname='fk_rutinas_entrenador' LIMIT 1")).fetchone()
                            if not has:
                                db.session.execute(text('ALTER TABLE rutinas ADD CONSTRAINT fk_rutinas_entrenador FOREIGN KEY (entrenador_id) REFERENCES entrenadores(id)'))
                        except Exception:
                            db.session.rollback()
                        try:
                            db.session.commit()
                        except Exception:
                            db.session.rollback()
                except Exception:
                    db.session.rollback()
            # Reintentar la consulta una vez
            try:
                rutinas = Rutina.query.filter_by(entrenador_id=entrenador.id).order_by(Rutina.creado_en.desc()).all()
            except Exception as e2:
                app.logger.exception('listar_rutinas: still failing after repair')
                return jsonify({'error': 'db error', 'detail': str(e2)}), 500

        result = []
        for r in rutinas:
            creado_val = None
            try:
                creado_val = r.creado_en.isoformat() if getattr(r, 'creado_en', None) else None
            except Exception:
                creado_val = None
            result.append({'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion, 'objetivo_principal': getattr(r, 'objetivo_principal', None), 'enfoque_rutina': getattr(r, 'enfoque_rutina', None), 'cualidades_clave': getattr(r, 'cualidades_clave', None), 'duracion_frecuencia': getattr(r, 'duracion_frecuencia', None), 'material_requerido': getattr(r, 'material_requerido', None), 'instrucciones_estructurales': getattr(r, 'instrucciones_estructurales', None), 'nivel': r.nivel, 'es_publica': r.es_publica, 'creado_en': creado_val, 'link_url': getattr(r, 'link_url', None)})
        return jsonify(result), 200
    except Exception as exc:
        # Log and return JSON diagnostic in development
        app.logger.exception('listar_rutinas: unexpected top-level error')
        return jsonify({'error': 'internal', 'detail': str(exc)}), 500


@app.route('/api/rutinas/public', methods=['GET'])
def listar_rutinas_publicas():
    """Devuelve rutinas públicas (es_publica == True) ordenadas por creación.
    Endpoint público: no requiere JWT. Se intenta ser resiliente ante fallos
    de esquema similar a `listar_rutinas`.
    """
    try:
        try:
            # Support optional filtering by nivel (e.g. ?nivel=principiante)
            nivel = request.args.get('nivel')
            q = Rutina.query.filter_by(es_publica=True)
            if nivel:
                q = q.filter(Rutina.nivel == nivel)
            rutinas = q.order_by(Rutina.creado_en.desc()).all()
        except Exception as e:
            # intento de reparación ligera
            err_str = str(e)
            app.logger.exception('listar_rutinas_publicas: query failed, attempting repair')
            if 'UndefinedColumn' in err_str or ('column' in err_str and 'does not exist' in err_str) or 'no such column' in err_str:
                try:
                    with app.app_context():
                        db.create_all()
                        expected_cols = {
                            'entrenador_id': 'INTEGER',
                            'nombre': 'VARCHAR(200)',
                            'descripcion': 'TEXT',
                            'nivel': 'VARCHAR(50)',
                            'es_publica': 'BOOLEAN',
                            'creado_en': 'TIMESTAMP'
                        }
                        for c, ttype in expected_cols.items():
                            try:
                                db.session.execute(text(f"ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS {c} {ttype}"))
                            except Exception:
                                pass
                        try:
                            db.session.commit()
                        except Exception:
                            db.session.rollback()
                except Exception:
                    db.session.rollback()
            # reintentar una vez
            try:
                rutinas = Rutina.query.filter_by(es_publica=True).order_by(Rutina.creado_en.desc()).all()
            except Exception as e2:
                app.logger.exception('listar_rutinas_publicas: still failing after repair')
                return jsonify({'error': 'db error', 'detail': str(e2)}), 500

        result = []
        for r in rutinas:
            creado_val = None
            try:
                creado_val = r.creado_en.isoformat() if getattr(r, 'creado_en', None) else None
            except Exception:
                creado_val = None
            # intentar obtener nombre del entrenador si existe y sólo mostrar si el usuario está activo
            entrenador_nombre = None
            try:
                ent = Entrenador.query.filter_by(id=r.entrenador_id).first()
                # skip rutinas if entrenador was deleted or its usuario is missing/inactive
                if not ent or not getattr(ent, 'usuario', None) or getattr(ent.usuario, 'activo', True) is False:
                    continue
                entrenador_nombre = ent.usuario.nombre
            except Exception:
                entrenador_nombre = None
            result.append({'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion, 'objetivo_principal': getattr(r, 'objetivo_principal', None), 'enfoque_rutina': getattr(r, 'enfoque_rutina', None), 'cualidades_clave': getattr(r, 'cualidades_clave', None), 'duracion_frecuencia': getattr(r, 'duracion_frecuencia', None), 'material_requerido': getattr(r, 'material_requerido', None), 'instrucciones_estructurales': getattr(r, 'instrucciones_estructurales', None), 'seccion_descripcion': getattr(r, 'seccion_descripcion', None), 'nivel': r.nivel, 'es_publica': r.es_publica, 'creado_en': creado_val, 'entrenador_nombre': entrenador_nombre, 'entrenador_id': r.entrenador_id, 'entrenador_usuario_id': getattr(ent, 'usuario_id', None) if ent else None, 'link_url': getattr(r, 'link_url', None)})
        return jsonify(result), 200
    except Exception as e:
        app.logger.exception('listar_rutinas_publicas: unexpected failure')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/rutinas/<int:rutina_id>', methods=['GET'])
def obtener_rutina_publica(rutina_id):
    """Devuelve la rutina por id si es pública. Si no es pública, devuelve 403.
    Endpoint público para que clientes puedan ver detalle sin autenticación.
    """
    try:
        rutina = Rutina.query.filter_by(id=rutina_id).first()
        if not rutina:
            return jsonify({'error': 'rutina not found'}), 404
        if not getattr(rutina, 'es_publica', False):
            # Rutina not public: allow access only if the requester is authorized.
            # Authorization rules mirror those for plans:
            # - Admin users (role == 'admin') may view.
            # - The entrenador owner may view.
            # - A cliente with an accepted SolicitudPlan for this rutina may view.
            # Otherwise return 403.
            try:
                auth_header = request.headers.get('Authorization', '')
                token_payload = None
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ', 1)[1]
                    try:
                        from auth import decode_token
                        token_payload = decode_token(token)
                    except Exception:
                        token_payload = None

                if token_payload:
                    # admin bypass
                    if token_payload.get('role') == 'admin':
                        pass
                    else:
                        from database.database import Entrenador, Cliente, SolicitudPlan
                        token_user_id = token_payload.get('user_id')
                        allowed = False
                        # trainer owner check
                        try:
                            entrenador = Entrenador.query.filter_by(id=getattr(rutina, 'entrenador_id', None)).first()
                            if entrenador and entrenador.usuario_id == token_user_id:
                                allowed = True
                        except Exception:
                            allowed = False

                        # cliente accepted solicitud check
                        if not allowed:
                            try:
                                cliente = Cliente.query.filter_by(usuario_id=token_user_id).first()
                                if cliente:
                                    sol = SolicitudPlan.query.filter_by(rutina_id=rutina.id, cliente_id=cliente.id, estado='aceptado').first()
                                    if sol:
                                        allowed = True
                            except Exception:
                                allowed = False

                        if not allowed:
                            return jsonify({'error': 'forbidden: rutina not public'}), 403
                else:
                    return jsonify({'error': 'forbidden: rutina not public'}), 403
            except Exception as e:
                app.logger.exception('authorization check for obtener_rutina_publica failed')
                return jsonify({'error': 'internal', 'detail': str(e)}), 500

        creado_val = None
        try:
            creado_val = rutina.creado_en.isoformat() if getattr(rutina, 'creado_en', None) else None
        except Exception:
            creado_val = None

        entrenador_nombre = None
        entrenador_id = getattr(rutina, 'entrenador_id', None)
        entrenador_usuario_id = None
        try:
            # Be defensive: avoid touching relationship attributes that may trigger unexpected errors
            ent = Entrenador.query.filter_by(id=entrenador_id).first() if entrenador_id else None
            if ent:
                entrenador_usuario_id = getattr(ent, 'usuario_id', None)
                if entrenador_usuario_id:
                    try:
                        # Query Usuario.nombre directly to avoid relying on relationship attributes
                        from database.database import Usuario
                        user = Usuario.query.with_entities(Usuario.nombre).filter_by(id=entrenador_usuario_id).first()
                        if user:
                            entrenador_nombre = getattr(user, 'nombre', None)
                    except Exception:
                        entrenador_nombre = None
        except Exception:
            entrenador_nombre = None

        return jsonify({'id': rutina.id, 'nombre': rutina.nombre, 'descripcion': rutina.descripcion, 'objetivo_principal': getattr(rutina, 'objetivo_principal', None), 'enfoque_rutina': getattr(rutina, 'enfoque_rutina', None), 'cualidades_clave': getattr(rutina, 'cualidades_clave', None), 'duracion_frecuencia': getattr(rutina, 'duracion_frecuencia', None), 'material_requerido': getattr(rutina, 'material_requerido', None), 'instrucciones_estructurales': getattr(rutina, 'instrucciones_estructurales', None), 'seccion_descripcion': getattr(rutina, 'seccion_descripcion', None), 'nivel': rutina.nivel, 'es_publica': rutina.es_publica, 'creado_en': creado_val, 'entrenador_nombre': entrenador_nombre, 'entrenador_id': entrenador_id, 'entrenador_usuario_id': entrenador_usuario_id, 'link_url': getattr(rutina, 'link_url', None)}), 200
    except Exception as e:
        app.logger.exception('obtener_rutina_publica failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


# Ruta pública alternativa y explícita para detalle de rutina, evita conflicto con
# rutas que aceptan `entrenador_usuario_id` en la misma posición de URL.
@app.route('/api/rutinas/public/<int:rutina_id>', methods=['GET'])
def obtener_rutina_publica_explicit(rutina_id):
    try:
        rutina = Rutina.query.filter_by(id=rutina_id).first()
        if not rutina:
            return jsonify({'error': 'rutina not found'}), 404
        if not getattr(rutina, 'es_publica', False):
            # Apply same authorization rules as for plans: admin, owner entrenador,
            # or cliente with accepted SolicitudPlan may view non-public rutinas.
            try:
                auth_header = request.headers.get('Authorization', '')
                token_payload = None
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ', 1)[1]
                    try:
                        from auth import decode_token
                        token_payload = decode_token(token)
                    except Exception:
                        token_payload = None

                if token_payload:
                    if token_payload.get('role') == 'admin':
                        pass
                    else:
                        from database.database import Entrenador, Cliente, SolicitudPlan
                        token_user_id = token_payload.get('user_id')
                        allowed = False
                        try:
                            entrenador = Entrenador.query.filter_by(id=getattr(rutina, 'entrenador_id', None)).first()
                            if entrenador and entrenador.usuario_id == token_user_id:
                                allowed = True
                        except Exception:
                            allowed = False
                        if not allowed:
                            try:
                                cliente = Cliente.query.filter_by(usuario_id=token_user_id).first()
                                if cliente:
                                    sol = SolicitudPlan.query.filter_by(rutina_id=rutina.id, cliente_id=cliente.id, estado='aceptado').first()
                                    if sol:
                                        allowed = True
                            except Exception:
                                allowed = False
                        if not allowed:
                            return jsonify({'error': 'forbidden: rutina not public'}), 403
                else:
                    return jsonify({'error': 'forbidden: rutina not public'}), 403
            except Exception as e:
                app.logger.exception('authorization check for obtener_rutina_publica_explicit failed')
                return jsonify({'error': 'internal', 'detail': str(e)}), 500

        creado_val = None
        try:
            creado_val = rutina.creado_en.isoformat() if getattr(rutina, 'creado_en', None) else None
        except Exception:
            creado_val = None

        entrenador_nombre = None
        entrenador_id = getattr(rutina, 'entrenador_id', None)
        entrenador_usuario_id = None
        try:
            ent = Entrenador.query.filter_by(id=entrenador_id).first() if entrenador_id else None
            if ent:
                entrenador_usuario_id = getattr(ent, 'usuario_id', None)
                entrenador_nombre = getattr(ent.usuario, 'nombre', None) if getattr(ent, 'usuario', None) else None
        except Exception:
            entrenador_nombre = None

        return jsonify({'id': rutina.id, 'nombre': rutina.nombre, 'descripcion': rutina.descripcion, 'objetivo_principal': getattr(rutina, 'objetivo_principal', None), 'enfoque_rutina': getattr(rutina, 'enfoque_rutina', None), 'cualidades_clave': getattr(rutina, 'cualidades_clave', None), 'duracion_frecuencia': getattr(rutina, 'duracion_frecuencia', None), 'material_requerido': getattr(rutina, 'material_requerido', None), 'instrucciones_estructurales': getattr(rutina, 'instrucciones_estructurales', None), 'seccion_descripcion': getattr(rutina, 'seccion_descripcion', None), 'nivel': rutina.nivel, 'es_publica': rutina.es_publica, 'creado_en': creado_val, 'entrenador_nombre': entrenador_nombre, 'entrenador_id': entrenador_id, 'entrenador_usuario_id': entrenador_usuario_id, 'link_url': getattr(rutina, 'link_url', None)}), 200
    except Exception as e:
        app.logger.exception('obtener_rutina_publica_explicit failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


# Defensive: catch non-integer IDs requested against the public rutina path
# Some frontend clients accidentally request `/api/rutinas/public/null` when
# no id is available — Flask's int route won't match and the request would
# normally return 404. In production we observed this reaching the app and
# resulting in a generic 500 response. Provide a clearer 400 response here.
@app.route('/api/rutinas/public/<rutina_id>', methods=['GET'])
def obtener_rutina_publica_public_id_guard(rutina_id):
    # If the path segment is not an integer, respond with a helpful 400
    try:
        int(rutina_id)
    except Exception:
        app.logger.info('Invalid rutina_id path received for public endpoint: %s', rutina_id)
        return jsonify({'error': 'invalid rutina id'}), 400
    # If it's an integer string, delegate to the explicit int route handler
    return obtener_rutina_publica_explicit(int(rutina_id))


@app.route('/api/rutinas/<int:rutina_id>/seguir', methods=['POST'])
@jwt_required
def seguir_rutina(rutina_id):
    """Asocia la rutina al cliente autenticado (guardar/seguir rutina).
    Crea una tabla ligera `cliente_rutina` si no existe y añade la relación
    evitando duplicados. Requiere token JWT y que el usuario tenga una fila
    `Cliente` asociada a su `usuario_id`.
    """
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    try:
        cliente = Cliente.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        cliente = None
    # If the authenticated user doesn't yet have a Cliente row, create it automatically.
    # This makes the UX smoother for users who registered but whose Cliente row wasn't provisioned.
    if not cliente:
        try:
            cliente = Cliente(usuario_id=token_user_id)
            db.session.add(cliente)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.exception('seguir_rutina: failed creating Cliente row')
            return jsonify({'error': 'cliente not found and could not be created', 'detail': str(e)}), 500

    try:
        rutina = Rutina.query.filter_by(id=rutina_id).first()
    except Exception:
        rutina = None
    if not rutina:
        return jsonify({'error': 'rutina not found'}), 404

    try:
        # Ensure lightweight join table exists. Use DB-native CREATE TABLE IF NOT EXISTS
        # to avoid needing full migrations in many environments.
        with app.app_context():
            try:
                db.session.execute(text('CREATE TABLE IF NOT EXISTS cliente_rutina (cliente_id INTEGER NOT NULL, rutina_id INTEGER NOT NULL, PRIMARY KEY (cliente_id, rutina_id))'))
            except Exception:
                # table creation might fail on restricted DBs; continue and attempt insert
                pass

            # Insert only if not exists (works in Postgres and SQLite via SELECT-WHERE NOT EXISTS pattern)
            insert_sql = text('INSERT INTO cliente_rutina (cliente_id, rutina_id) SELECT :cid, :rid WHERE NOT EXISTS (SELECT 1 FROM cliente_rutina WHERE cliente_id = :cid AND rutina_id = :rid)')
            db.session.execute(insert_sql, {'cid': cliente.id, 'rid': rutina.id})
            db.session.commit()
        return jsonify({'message': 'rutina guardada'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('seguir_rutina failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/rutinas/<int:rutina_id>/seguir', methods=['DELETE'])
@jwt_required
def dejar_de_seguir_rutina(rutina_id):
    """Elimina la relación cliente_rutina para el cliente autenticado.
    Si la relación no existe, devuelve 200 (idempotente).
    """
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    try:
        cliente = Cliente.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        cliente = None

    if not cliente:
        return jsonify({'error': 'cliente not found'}), 404

    try:
        # Attempt to delete the row from cliente_rutina; be lenient if table missing
        try:
            delete_sql = text('DELETE FROM cliente_rutina WHERE cliente_id = :cid AND rutina_id = :rid')
            db.session.execute(delete_sql, {'cid': cliente.id, 'rid': rutina_id})
            db.session.commit()
        except Exception:
            db.session.rollback()
            # If the table doesn't exist or deletion failed, return success (idempotent)
            return jsonify({'message': 'no-op'}), 200

        return jsonify({'message': 'rutina eliminada de guardadas'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('dejar_de_seguir_rutina failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/rutinas/mis', methods=['GET'])
@jwt_required
def listar_mis_rutinas():
    """Devuelve las rutinas guardadas por el cliente autenticado.
    Requiere JWT. Intenta ser resiliente ante ausencia de la tabla cliente_rutina.
    """
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    try:
        cliente = Cliente.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        cliente = None

    if not cliente:
        # create cliente row for the user if missing to keep behavior consistent
        try:
            cliente = Cliente(usuario_id=token_user_id)
            db.session.add(cliente)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'cliente not found'}), 404

    try:
        # Ensure join table exists (best-effort)
        try:
            db.session.execute(text('CREATE TABLE IF NOT EXISTS cliente_rutina (cliente_id INTEGER NOT NULL, rutina_id INTEGER NOT NULL, PRIMARY KEY (cliente_id, rutina_id))'))
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Try raw SQL join first (fast). If it fails (missing table/permission),
        # fall back to an ORM-based query using SolicitudPlan -> Rutina.
        try:
            # Select all descriptive columns so frontend always receives full rutina data
            q = text(
                'SELECT r.id, r.nombre, r.descripcion, r.nivel, r.es_publica, r.creado_en, r.link_url as link_url, '
                'r.seccion_descripcion, r.objetivo_principal, r.enfoque_rutina, r.cualidades_clave, '
                'r.duracion_frecuencia, r.material_requerido, r.instrucciones_estructurales '
                'FROM rutinas r JOIN cliente_rutina cr ON cr.rutina_id = r.id '
                'WHERE cr.cliente_id = :cid ORDER BY r.creado_en DESC'
            )
            rows = db.session.execute(q, {'cid': cliente.id}).fetchall()
            result = []
            for r in rows:
                creado_val = None
                try:
                    # r.creado_en may be a datetime or string
                    creado_val = r['creado_en'].isoformat() if getattr(r['creado_en'], 'isoformat', None) else str(r['creado_en'])
                except Exception:
                    creado_val = None
                # Build a safe dict even if some columns are missing
                result.append({
                    'id': r['id'],
                    'nombre': r['nombre'],
                    'descripcion': r['descripcion'],
                    'nivel': r['nivel'] if 'nivel' in getattr(r, 'keys', lambda: [])() else (r.get('nivel') if hasattr(r, 'get') else None),
                    'es_publica': r['es_publica'] if 'es_publica' in getattr(r, 'keys', lambda: [])() else None,
                    'creado_en': creado_val,
                    'link_url': r['link_url'] if 'link_url' in getattr(r, 'keys', lambda: [])() else None,
                    'seccion_descripcion': r['seccion_descripcion'] if 'seccion_descripcion' in getattr(r, 'keys', lambda: [])() else None,
                    'objetivo_principal': r['objetivo_principal'] if 'objetivo_principal' in getattr(r, 'keys', lambda: [])() else None,
                    'enfoque_rutina': r['enfoque_rutina'] if 'enfoque_rutina' in getattr(r, 'keys', lambda: [])() else None,
                    'cualidades_clave': r['cualidades_clave'] if 'cualidades_clave' in getattr(r, 'keys', lambda: [])() else None,
                    'duracion_frecuencia': r['duracion_frecuencia'] if 'duracion_frecuencia' in getattr(r, 'keys', lambda: [])() else None,
                    'material_requerido': r['material_requerido'] if 'material_requerido' in getattr(r, 'keys', lambda: [])() else None,
                    'instrucciones_estructurales': r['instrucciones_estructurales'] if 'instrucciones_estructurales' in getattr(r, 'keys', lambda: [])() else None
                })
            return jsonify(result), 200
        except Exception:
            # Log and attempt an ORM fallback: use SolicitudPlan entries to infer rutinas
            app.logger.exception('listar_mis_rutinas: raw SQL failed, attempting ORM fallback')
            db.session.rollback()
            try:
                from database.database import SolicitudPlan
                # Get rutina_ids from solicitudes for this cliente as a reasonable fallback
                sols = SolicitudPlan.query.filter_by(cliente_id=cliente.id).order_by(SolicitudPlan.creado_en.desc()).all()
                rutina_ids = [s.rutina_id for s in sols if getattr(s, 'rutina_id', None)]
                result = []
                if rutina_ids:
                        rutinas = Rutina.query.filter(Rutina.id.in_(rutina_ids)).order_by(Rutina.creado_en.desc()).all()
                        for r in rutinas:
                            creado_val = None
                            try:
                                creado_val = r.creado_en.isoformat() if getattr(r, 'creado_en', None) else None
                            except Exception:
                                creado_val = None
                            result.append({
                                'id': r.id,
                                'nombre': r.nombre,
                                'descripcion': r.descripcion,
                                'nivel': getattr(r, 'nivel', None),
                                'es_publica': getattr(r, 'es_publica', None),
                                'creado_en': creado_val,
                                'link_url': getattr(r, 'link_url', None),
                                'seccion_descripcion': getattr(r, 'seccion_descripcion', None),
                                'objetivo_principal': getattr(r, 'objetivo_principal', None),
                                'enfoque_rutina': getattr(r, 'enfoque_rutina', None),
                                'cualidades_clave': getattr(r, 'cualidades_clave', None),
                                'duracion_frecuencia': getattr(r, 'duracion_frecuencia', None),
                                'material_requerido': getattr(r, 'material_requerido', None),
                                'instrucciones_estructurales': getattr(r, 'instrucciones_estructurales', None)
                            })
                # If no rutina_ids or the fallback produced nothing, return empty list instead of 500
                return jsonify(result), 200
            except Exception:
                app.logger.exception('listar_mis_rutinas: ORM fallback also failed')
                # Return an empty list to avoid surfacing a 500 to the frontend for this user-facing call
        # Allow preflight OPTIONS for reactivate without auth so browsers can perform the CORS preflight.
        @app.route('/api/admin/usuarios/<int:usuario_id>/reactivar', methods=['OPTIONS'])
        def admin_reactivar_options(usuario_id):
            return ('', 200)
            # If the solicitud refers to a plan instead, try to include its nombre
            if not rutina_nombre and getattr(s, 'plan_id', None):
                try:
                    from database.database import PlanAlimenticio
                    p = PlanAlimenticio.query.filter_by(id=s.plan_id).first()
                    if p:
                        plan_nombre = getattr(p, 'nombre', None)
                except Exception:
                    plan_nombre = None
            # Favor rutina name, then plan name, else None
            display_nombre = rutina_nombre or plan_nombre or 'Sin nombre'
            result.append({'id': s.id, 'rutina_id': s.rutina_id, 'plan_id': s.plan_id, 'rutina_nombre': display_nombre, 'estado': s.estado, 'nota': s.nota, 'creado_en': creado})
        return jsonify(result), 200
    except Exception as e:
        app.logger.exception('listar_solicitudes_mis failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500



@app.route('/api/solicitudes/<int:solicitud_id>', methods=['DELETE'])
@jwt_required
def cancelar_solicitud(solicitud_id):
    """Permite al cliente cancelar (eliminar) su propia solicitud.
    Verifica que la solicitud pertenezca al cliente autenticado.
    """
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    try:
        cliente = Cliente.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        cliente = None
    if not cliente:
        return jsonify({'error': 'cliente not found'}), 404

    try:
        from database.database import SolicitudPlan
        s = SolicitudPlan.query.filter_by(id=solicitud_id).first()
        if not s:
            return jsonify({'error': 'solicitud not found'}), 404
        if s.cliente_id != cliente.id:
            return jsonify({'error': 'forbidden: not your solicitud'}), 403

        # Mark the solicitud as canceled instead of deleting it to keep history
        try:
            s.estado = 'cancelado'
            db.session.add(s)
            db.session.commit()
            return jsonify({'message': 'solicitud cancelada', 'id': s.id, 'estado': s.estado}), 200
        except Exception as e:
            db.session.rollback()
            app.logger.exception('cancelar_solicitud: db update failed')
            return jsonify({'error': 'db error', 'detail': str(e)}), 500
    except Exception as e:
        app.logger.exception('cancelar_solicitud failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/solicitudes/pendientes', methods=['GET'])
@jwt_required
def listar_solicitudes_pendientes():
    """Listado de solicitudes pendientes para el entrenador autenticado.
    Devuelve solo solicitudes cuyo plan/rutina pertenece al entrenador.
    """
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    try:
        entrenador = Entrenador.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        entrenador = None
    if not entrenador:
        return jsonify({'error': 'forbidden: not entrenador'}), 403

    try:
        from database.database import SolicitudPlan, PlanAlimenticio, Rutina
        # Find solicitudes with estado 'pendiente' where the related plan or rutina
        # belongs to this entrenador.
        # We'll query both sides defensively.
        result = []

        # solicitudes that reference plans owned by this entrenador
        try:
            plan_sols = db.session.query(SolicitudPlan).join(PlanAlimenticio, SolicitudPlan.plan_id == PlanAlimenticio.id).filter(PlanAlimenticio.entrenador_id == entrenador.id, SolicitudPlan.estado == 'pendiente').all()
        except Exception:
            plan_sols = []

        # solicitudes that reference rutinas owned by this entrenador
        try:
            rutina_sols = db.session.query(SolicitudPlan).join(Rutina, SolicitudPlan.rutina_id == Rutina.id).filter(Rutina.entrenador_id == entrenador.id, SolicitudPlan.estado == 'pendiente').all()
        except Exception:
            rutina_sols = []

        todos = list({s.id: s for s in (plan_sols + rutina_sols)}.values())
        for s in todos:
            creado = None
            try:
                creado = s.creado_en.isoformat() if getattr(s, 'creado_en', None) else None
            except Exception:
                creado = None
            rutina_nombre = None
            plan_nombre = None
            cliente_nombre = None
            try:
                if getattr(s, 'rutina_id', None):
                    r = Rutina.query.filter_by(id=s.rutina_id).first()
                    if r:
                        rutina_nombre = getattr(r, 'nombre', None)
            except Exception:
                rutina_nombre = None
            if not rutina_nombre and getattr(s, 'plan_id', None):
                try:
                    p = PlanAlimenticio.query.filter_by(id=s.plan_id).first()
                    if p:
                        plan_nombre = getattr(p, 'nombre', None)
                except Exception:
                    plan_nombre = None
            # attempt to include the cliente's usuario.nombre for clarity
            try:
                # prefer relationship if present
                if getattr(s, 'cliente', None) and getattr(s.cliente, 'usuario', None):
                    cliente_nombre = getattr(s.cliente.usuario, 'nombre', None)
                else:
                    # fallback: query Cliente -> Usuario
                    from database.database import Cliente, Usuario
                    c = Cliente.query.filter_by(id=getattr(s, 'cliente_id', None)).first()
                    if c:
                        u = Usuario.query.filter_by(id=getattr(c, 'usuario_id', None)).first()
                        if u:
                            cliente_nombre = getattr(u, 'nombre', None)
            except Exception:
                cliente_nombre = None
            display_nombre = rutina_nombre or plan_nombre or 'Sin nombre'
            result.append({'id': s.id, 'rutina_id': s.rutina_id, 'plan_id': s.plan_id, 'rutina_nombre': display_nombre, 'estado': s.estado, 'nota': s.nota, 'creado_en': creado, 'cliente_id': s.cliente_id, 'cliente_nombre': cliente_nombre})

        return jsonify(result), 200
    except Exception as e:
        app.logger.exception('listar_solicitudes_pendientes failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/solicitudes/<int:solicitud_id>', methods=['PUT'])
@jwt_required
def actualizar_solicitud_estado(solicitud_id):
    """Permite al entrenador aceptar/rechazar una solicitud que pertenece a uno de sus planes/rutinas.
    Body: { "estado": "aceptado" | "rechazado" | "cancelado" }
    """
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    try:
        entrenador = Entrenador.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        entrenador = None
    if not entrenador:
        return jsonify({'error': 'forbidden: not entrenador'}), 403

    data = request.get_json() or {}
    new_estado = data.get('estado')
    if new_estado not in ('aceptado', 'rechazado', 'cancelado'):
        return jsonify({'error': 'invalid estado'}), 400

    try:
        from database.database import SolicitudPlan, PlanAlimenticio, Rutina
        s = SolicitudPlan.query.filter_by(id=solicitud_id).first()
        if not s:
            return jsonify({'error': 'solicitud not found'}), 404

        # verify that the solicitud belongs to a plan/rutina owned by this entrenador
        owner_ok = False
        try:
            if getattr(s, 'plan_id', None):
                p = PlanAlimenticio.query.filter_by(id=s.plan_id).first()
                if p and getattr(p, 'entrenador_id', None) == entrenador.id:
                    owner_ok = True
        except Exception:
            pass
        try:
            if not owner_ok and getattr(s, 'rutina_id', None):
                r = Rutina.query.filter_by(id=s.rutina_id).first()
                if r and getattr(r, 'entrenador_id', None) == entrenador.id:
                    owner_ok = True
        except Exception:
            pass

        if not owner_ok:
            return jsonify({'error': 'forbidden: not owner'}), 403

        s.estado = new_estado
        db.session.add(s)
        db.session.commit()
        return jsonify({'message': 'estado actualizado', 'id': s.id, 'estado': s.estado}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('actualizar_solicitud_estado failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


# --- Plan alimenticio endpoints ---
@app.route('/api/planes', methods=['POST'])
@jwt_required
def crear_plan():
    """Entrenador crea un plan alimenticio.
    Body: { nombre, descripcion, contenido, es_publico }
    """
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    # Verify entrenador (defensive: catch DB errors here separately so we can log them)
    try:
        entrenador = Entrenador.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        app.logger.exception('crear_plan: entrenador lookup failed')
        return jsonify({'error': 'db error'}), 500
    if not entrenador:
        return jsonify({'error': 'forbidden: not entrenador'}), 403

    data = request.get_json() or {}
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    contenido = data.get('contenido')
    # Always keep new plans not-public by default; admin must approve to publish.
    # Ignore any client-supplied `es_publico` to enforce review workflow.
    es_publico = False

    if not nombre:
        # Required field missing
        return jsonify({'error': 'nombre required'}), 400

    # Log payload for debugging (temporary)
    try:
        app.logger.debug('crear_plan: payload=%s, entrenador_id=%s', data, getattr(entrenador, 'id', None))
    except Exception:
        # ignore logging errors
        pass

    try:
        from database.database import PlanAlimenticio
        plan = PlanAlimenticio(entrenador_id=entrenador.id, nombre=nombre, descripcion=descripcion, contenido=contenido, es_publico=es_publico)
        db.session.add(plan)
        db.session.commit()
        # Create a ContentReview entry so admins can review this new plan
        try:
            from database.database import ContentReview
            review = ContentReview(tipo='plan', content_id=plan.id, estado='pendiente', creado_por=token_user_id)
            db.session.add(review)
            db.session.commit()
        except Exception:
            # best-effort: log failure to create ContentReview but do not fail plan creation
            try:
                logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
                os.makedirs(logs_dir, exist_ok=True)
                with open(os.path.join(logs_dir, 'crear_plan_review_error.log'), 'a', encoding='utf-8') as fh:
                    fh.write('----\n')
                    fh.write(f'TIME: {datetime.utcnow().isoformat()}\n')
                    fh.write(f'PLAN_ID: {getattr(plan, "id", None)}\n')
                    fh.write(f'CREADO_POR: {token_user_id}\n')
                    import traceback as _tb
                    fh.write('TRACEBACK:\n')
                    fh.write(_tb.format_exc())
                    fh.write('\n')
            except Exception:
                app.logger.exception('crear_plan: failed logging review error')
        return jsonify({'message': 'plan creado', 'id': plan.id}), 201
    except Exception as e:
        db.session.rollback()
        # Log exception with payload to help diagnose production failures
        app.logger.exception('crear_plan failed during insert/commit: payload=%s', data)
        # Return minimal diagnostic: include detail only in development
        is_prod = bool(os.getenv('DATABASE_URL'))
        if is_prod:
            return jsonify({'error': 'db error'}), 500
        else:
            return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/planes/generate', methods=['POST'])
@jwt_required
def generar_plan():
    """Generador básico de planes alimenticios (RF08).
    Body: { cliente_id (opcional), objetivo (opcional), calorias (opcional), save: bool }
    Si save=true y el usuario es entrenador, persistimos el plan y devolvemos su id.
    """
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401
    try:
        entrenador = Entrenador.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        entrenador = None
    if not entrenador:
        return jsonify({'error': 'forbidden: not entrenador'}), 403

    data = request.get_json() or {}
    objetivo = (data.get('objetivo') or 'mantenimiento')
    calorias = data.get('calorias')
    cliente_id = data.get('cliente_id')
    save = bool(data.get('save', False))

    # Simple heuristic: if no calorias provided, try to estimate from cliente measurements
    if not calorias and cliente_id:
        try:
            cliente = Cliente.query.filter_by(id=int(cliente_id)).first()
            if cliente and getattr(cliente, 'peso', None):
                # TDEE rough estimate: 24 * peso * 1.2 (sedentario)
                calorias = int(24 * float(getattr(cliente, 'peso', 0)) * 1.2)
        except Exception:
            calorias = None

    if not calorias:
        # fallback default
        calorias = 2000

    # Very simple generated content (use triple-quoted f-string to avoid escaping issues)
    contenido = f"""Plan generado: objetivo={objetivo}
Calorías diarias objetivo: {calorias}

Desglose sugerido:
- Desayuno: 25%
- Almuerzo: 35%
- Cena: 30%
- Snacks: 10%

Ejemplo de comidas:
- Desayuno: Avena + fruta + clara
- Almuerzo: Proteína magra + arroz integral + ensalada
- Cena: Verduras + pescado/pollo
"""
    nombre = f"Plan generado ({objetivo})"

    if save:
        try:
            from database.database import PlanAlimenticio
            plan = PlanAlimenticio(entrenador_id=entrenador.id, nombre=nombre, descripcion=f'Plan generado automáticamente para cliente {cliente_id}', contenido=contenido, es_publico=False)
            db.session.add(plan)
            db.session.commit()
            return jsonify({'message': 'plan generado y guardado', 'id': plan.id}), 201
        except Exception as e:
            db.session.rollback()
            app.logger.exception('generar_plan failed to save')
            return jsonify({'error': 'db error', 'detail': str(e)}), 500

    # Return generated plan content without persisting
    return jsonify({'nombre': nombre, 'contenido': contenido, 'calorias': calorias, 'objetivo': objetivo}), 200


@app.route('/api/planes', methods=['GET'])
def listar_planes_publicos():
    try:
        planes = []
        try:
            # import model lazily to avoid circular imports during app init
            from database.database import PlanAlimenticio
            planes = PlanAlimenticio.query.filter_by(es_publico=True).order_by(PlanAlimenticio.creado_en.desc()).all()
        except Exception:
            # attempt to create table if missing
            try:
                with app.app_context():
                    db.create_all()
            except Exception:
                pass
            try:
                planes = PlanAlimenticio.query.filter_by(es_publico=True).order_by(PlanAlimenticio.creado_en.desc()).all()
            except Exception as e:
                app.logger.exception('listar_planes_publicos failed')
                return jsonify({'error': 'db error', 'detail': str(e)}), 500

        result = []
        for p in planes:
            creado = None
            try:
                creado = p.creado_en.isoformat() if getattr(p, 'creado_en', None) else None
            except Exception:
                creado = None
            entrenador_nombre = None
            try:
                ent = Entrenador.query.filter_by(id=p.entrenador_id).first()
                # skip plans if entrenador was deleted or its usuario is missing/inactive
                if not ent or not getattr(ent, 'usuario', None) or getattr(ent.usuario, 'activo', True) is False:
                    # do not expose plans that belong to non-existent or deactivated trainers
                    continue
                entrenador_nombre = getattr(ent.usuario, 'nombre', None)
            except Exception:
                entrenador_nombre = None
            result.append({'id': p.id, 'nombre': p.nombre, 'descripcion': p.descripcion, 'contenido': p.contenido, 'es_publico': p.es_publico, 'creado_en': creado, 'entrenador_nombre': entrenador_nombre, 'entrenador_id': p.entrenador_id})
        return jsonify(result), 200
    except Exception as e:
        app.logger.exception('listar_planes_publicos unexpected')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500



@app.route('/api/planes/<int:plan_id>', methods=['GET'])
def obtener_plan_publico(plan_id):
    """Devuelve detalle de un plan alimenticio por id. Público si es_publico==True.
    Endpoint público para que clientes puedan ver detalle sin autenticación.
    """
    try:
        from database.database import PlanAlimenticio
        plan = PlanAlimenticio.query.filter_by(id=plan_id).first()
        if not plan:
            return jsonify({'error': 'plan not found'}), 404
        if not getattr(plan, 'es_publico', False):
            # Plan not public: allow access only if the requester is authorized.
            # Authorization rules:
            # - Admin users (role == 'admin') may view.
            # - The entrenador owner may view.
            # - A cliente with an accepted SolicitudPlan for this plan may view.
            # Otherwise return 403.
            try:
                auth_header = request.headers.get('Authorization', '')
                token_payload = None
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ', 1)[1]
                    try:
                        from auth import decode_token
                        token_payload = decode_token(token)
                    except Exception:
                        token_payload = None

                # If token present and decoded, check roles and relations
                if token_payload:
                    # admin bypass
                    if token_payload.get('role') == 'admin':
                        pass
                    else:
                        # import models lazily
                        from database.database import Entrenador, Cliente, SolicitudPlan, Usuario
                        token_user_id = token_payload.get('user_id')
                        allowed = False
                        # trainer owner check
                        try:
                            entrenador = Entrenador.query.filter_by(id=getattr(plan, 'entrenador_id', None)).first()
                            if entrenador and entrenador.usuario_id == token_user_id:
                                allowed = True
                        except Exception:
                            allowed = False

                        # cliente accepted solicitud check
                        if not allowed:
                            try:
                                cliente = Cliente.query.filter_by(usuario_id=token_user_id).first()
                                if cliente:
                                    sol = SolicitudPlan.query.filter_by(plan_id=plan.id, cliente_id=cliente.id, estado='aceptado').first()
                                    if sol:
                                        allowed = True
                            except Exception:
                                allowed = False

                        if not allowed:
                            return jsonify({'error': 'forbidden: plan not public'}), 403
                else:
                    # no valid token -> forbidden
                    return jsonify({'error': 'forbidden: plan not public'}), 403
            except Exception as e:
                app.logger.exception('authorization check for obtener_plan_publico failed')
                return jsonify({'error': 'internal', 'detail': str(e)}), 500

        creado_val = None
        try:
            creado_val = plan.creado_en.isoformat() if getattr(plan, 'creado_en', None) else None
        except Exception:
            creado_val = None

        entrenador_nombre = None
        try:
            ent = Entrenador.query.filter_by(id=plan.entrenador_id).first()
            if ent and getattr(ent, 'usuario', None):
                entrenador_nombre = ent.usuario.nombre
        except Exception:
            entrenador_nombre = None

        return jsonify({'id': plan.id, 'nombre': plan.nombre, 'descripcion': plan.descripcion, 'contenido': plan.contenido, 'es_publico': plan.es_publico, 'creado_en': creado_val, 'entrenador_nombre': entrenador_nombre, 'entrenador_id': plan.entrenador_id}), 200
    except Exception as e:
        app.logger.exception('obtener_plan_publico failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500



@app.route('/api/planes/mis', methods=['GET'])
@jwt_required
def listar_planes_mis():
    """Devuelve los planes creados por el entrenador autenticado.
    Requiere JWT y que el usuario tenga rol de entrenador (fila Entrenador).
    """
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    try:
        entrenador = Entrenador.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        entrenador = None

    if not entrenador:
        return jsonify({'error': 'forbidden: not entrenador'}), 403

    try:
        from database.database import PlanAlimenticio
        planes = PlanAlimenticio.query.filter_by(entrenador_id=entrenador.id).order_by(PlanAlimenticio.creado_en.desc()).all()
        result = []
        for p in planes:
            creado = None
            try:
                creado = p.creado_en.isoformat() if getattr(p, 'creado_en', None) else None
            except Exception:
                creado = None
            result.append({'id': p.id, 'nombre': p.nombre, 'descripcion': p.descripcion, 'contenido': p.contenido, 'es_publico': p.es_publico, 'creado_en': creado, 'entrenador_id': p.entrenador_id})
        return jsonify(result), 200
    except Exception as e:
        app.logger.exception('listar_planes_mis failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500



@app.route('/api/planes/<int:plan_id>', methods=['PUT'])
@jwt_required
def actualizar_plan(plan_id):
    """Actualizar un plan alimenticio. Solo el entrenador propietario puede modificarlo."""
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    try:
        entrenador = Entrenador.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        entrenador = None
    if not entrenador:
        return jsonify({'error': 'forbidden: not entrenador'}), 403

    try:
        from database.database import PlanAlimenticio
        plan = PlanAlimenticio.query.filter_by(id=plan_id).first()
        if not plan:
            return jsonify({'error': 'plan not found'}), 404
        if plan.entrenador_id != entrenador.id:
            return jsonify({'error': 'forbidden: not owner'}), 403

        data = request.get_json() or {}
        if 'nombre' in data:
            plan.nombre = data.get('nombre')
        if 'descripcion' in data:
            plan.descripcion = data.get('descripcion')
        if 'contenido' in data:
            plan.contenido = data.get('contenido')
        if 'es_publico' in data:
            plan.es_publico = bool(data.get('es_publico'))

        db.session.add(plan)
        db.session.commit()
        return jsonify({'message': 'plan actualizado', 'id': plan.id}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('actualizar_plan failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/planes/<int:plan_id>', methods=['DELETE'])
@jwt_required
def eliminar_plan(plan_id):
    """Eliminar un plan alimenticio. Solo el entrenador propietario puede eliminarlo."""
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    try:
        entrenador = Entrenador.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        entrenador = None
    if not entrenador:
        return jsonify({'error': 'forbidden: not entrenador'}), 403

    try:
        from database.database import PlanAlimenticio
        plan = PlanAlimenticio.query.filter_by(id=plan_id).first()
        if not plan:
            return jsonify({'error': 'plan not found'}), 404
        if plan.entrenador_id != entrenador.id:
            return jsonify({'error': 'forbidden: not owner'}), 403

        db.session.delete(plan)
        db.session.commit()
        return jsonify({'message': 'plan eliminado', 'id': plan_id}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('eliminar_plan failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/planes/<int:plan_id>/solicitar', methods=['POST'])
@jwt_required
def solicitar_plan_por_plan(plan_id):
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401
    try:
        cliente = Cliente.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        cliente = None
    if not cliente:
        try:
            cliente = Cliente(usuario_id=token_user_id)
            db.session.add(cliente)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'cliente not found'}), 404

    try:
        # Ensure the model is imported in this scope (avoid NameError when not lazily imported)
        from database.database import PlanAlimenticio
        plan = PlanAlimenticio.query.filter_by(id=plan_id).first()
        # Ensure solicitudes_plan table exists and has expected columns (compat with older test DBs)
        try:
            with app.app_context():
                # portable create for SQLite testing and Postgres
                try:
                    db.session.execute(text("CREATE TABLE IF NOT EXISTS solicitudes_plan (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER NOT NULL, rutina_id INTEGER, plan_id INTEGER, estado VARCHAR(50) DEFAULT 'pendiente', nota TEXT, creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                # try to add missing columns in case table was created with older schema
                try:
                    db.session.execute(text("ALTER TABLE solicitudes_plan ADD COLUMN plan_id INTEGER"))
                    db.session.execute(text("ALTER TABLE solicitudes_plan ADD COLUMN rutina_id INTEGER"))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        except Exception:
            # non-fatal; we'll try the ORM insert and handle errors
            pass
        if not plan:
            return jsonify({'error': 'plan not found'}), 404
        from database.database import SolicitudPlan
        # Create plan-based solicitud in 'pendiente' state so the entrenador
        # must accept or reject it via the pending solicitudes endpoint.
        s = SolicitudPlan(cliente_id=cliente.id, plan_id=plan.id, estado='pendiente')
        db.session.add(s)
        try:
            db.session.commit()
        except Exception as commit_exc:
            # If the existing DB schema has rutina_id NOT NULL or is missing plan_id,
            # attempt a lightweight table rebuild to correct the schema, then retry.
            db.session.rollback()
            app.logger.exception('solicitar_plan_por_plan: commit failed, attempting table rebuild')
            try:
                with app.app_context():
                    # create new table with correct nullable columns
                    db.session.execute(text("CREATE TABLE IF NOT EXISTS solicitudes_plan_new (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER NOT NULL, rutina_id INTEGER, plan_id INTEGER, estado VARCHAR(50) DEFAULT 'pendiente', nota TEXT, creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
                    # copy minimal columns to new table, setting rutina_id/plan_id to NULL where needed
                    try:
                        db.session.execute(text("INSERT INTO solicitudes_plan_new (id, cliente_id, rutina_id, plan_id, estado, nota, creado_en) SELECT id, cliente_id, NULL AS rutina_id, NULL AS plan_id, estado, nota, creado_en FROM solicitudes_plan"))
                    except Exception:
                        # If copy fails (schema mismatch), ignore and continue — new table will be empty
                        pass
                    # replace old table
                    db.session.execute(text('DROP TABLE IF EXISTS solicitudes_plan'))
                    db.session.execute(text('ALTER TABLE solicitudes_plan_new RENAME TO solicitudes_plan'))
                    db.session.commit()
            except Exception:
                db.session.rollback()
            # retry insert once more
            db.session.add(s)
            db.session.commit()
        creado = None
        try:
            creado = s.creado_en.isoformat() if getattr(s, 'creado_en', None) else None
        except Exception:
            creado = None
        return jsonify({'message': 'solicitud creada', 'id': s.id, 'estado': s.estado, 'creado_en': creado}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.exception('solicitar_plan_por_plan failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/rutinas/<int:rutina_id>', methods=['PUT'])
@jwt_required
def actualizar_rutina(rutina_id):
    data = request.get_json() or {}
    header_user_id = request.jwt_payload.get('user_id')

    rutina = Rutina.query.filter_by(id=rutina_id).first()
    if not rutina:
        return jsonify({'error': 'rutina not found'}), 404

    # verificar que el token user_id corresponde al usuario del entrenador propietario
    entrenador = Entrenador.query.filter_by(id=rutina.entrenador_id).first()
    if not entrenador or entrenador.usuario_id != header_user_id:
        return jsonify({'error': 'forbidden: cannot modify this rutina'}), 403

    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    nivel = data.get('nivel')
    es_publica = data.get('es_publica')

    # detailed sections
    objetivo_principal = data.get('objetivo_principal')
    enfoque_rutina = data.get('enfoque_rutina')
    cualidades_clave = data.get('cualidades_clave')
    duracion_frecuencia = data.get('duracion_frecuencia')
    material_requerido = data.get('material_requerido')
    instrucciones_estructurales = data.get('instrucciones_estructurales')

    if nombre is not None:
        rutina.nombre = nombre
    if descripcion is not None:
        rutina.descripcion = descripcion
    if objetivo_principal is not None:
        rutina.objetivo_principal = objetivo_principal
    if enfoque_rutina is not None:
        rutina.enfoque_rutina = enfoque_rutina
    if cualidades_clave is not None:
        rutina.cualidades_clave = cualidades_clave
    if duracion_frecuencia is not None:
        rutina.duracion_frecuencia = duracion_frecuencia
    if material_requerido is not None:
        rutina.material_requerido = material_requerido
    if instrucciones_estructurales is not None:
        rutina.instrucciones_estructurales = instrucciones_estructurales
    if nivel is not None:
        rutina.nivel = nivel
    if es_publica is not None:
        rutina.es_publica = bool(es_publica)

    try:
        db.session.commit()
        return jsonify({'message': 'rutina actualizada', 'rutina': {'id': rutina.id, 'nombre': rutina.nombre, 'descripcion': rutina.descripcion, 'nivel': rutina.nivel, 'es_publica': rutina.es_publica, 'creado_en': rutina.creado_en.isoformat()}}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'db error', 'detail': str(e)}), 500



@app.route('/api/rutinas/<int:rutina_id>', methods=['DELETE'])
@jwt_required
def eliminar_rutina(rutina_id):
    header_user_id = request.jwt_payload.get('user_id')

    rutina = Rutina.query.filter_by(id=rutina_id).first()
    if not rutina:
        return jsonify({'error': 'rutina not found'}), 404

    entrenador = Entrenador.query.filter_by(id=rutina.entrenador_id).first()
    if not entrenador or entrenador.usuario_id != header_user_id:
        return jsonify({'error': 'forbidden: cannot delete this rutina'}), 403

    try:
        db.session.delete(rutina)
        db.session.commit()
        return jsonify({'message': 'rutina eliminada'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'db error', 'detail': str(e)}), 500



# ------------------ Admin endpoints (protected por role==admin) ------------------
@app.route('/api/admin/usuarios', methods=['GET'])
@jwt_required
def admin_list_users():
    # solo admin
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    try:
        from database.database import Usuario
        try:
            users = Usuario.query.order_by(Usuario.creado_en.desc()).all()
        except Exception as qe:
            # If the error is due to missing columns (e.g., usuarios.activo), try a safe repair
            try:
                from sqlalchemy.exc import ProgrammingError
                err_str = str(qe)
                if 'column usuarios.activo does not exist' in err_str or 'activo' in err_str or isinstance(qe, ProgrammingError):
                    # Attempt to add the missing column and retry once
                    try:
                        db.session.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT true"))
                        db.session.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS failed_attempts INTEGER DEFAULT 0"))
                        db.session.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP"))
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

                # Retry the ORM query once
                try:
                    users = Usuario.query.order_by(Usuario.creado_en.desc()).all()
                except Exception as qe2:
                    # As a robust fallback, perform a raw SQL select that only references known-safe tables/columns
                    # This helps the admin UI survive partial schema drift.
                    try:
                        # Use COALESCE on creado_en to ensure ORDER BY works even when column is NULL/missing
                        rows = db.session.execute(text("""
                            SELECT u.id, u.email, u.nombre, u.creado_en, u.activo,
                                CASE WHEN e.usuario_id IS NOT NULL THEN 'entrenador' WHEN c.usuario_id IS NOT NULL THEN 'cliente' ELSE 'usuario' END as role
                            FROM usuarios u
                            LEFT JOIN entrenadores e ON e.usuario_id = u.id
                            LEFT JOIN clientes c ON c.usuario_id = u.id
                            ORDER BY COALESCE(u.creado_en, to_timestamp(0)) DESC
                        """)).fetchall()

                        users = []
                        for rw in rows:
                            # Build a simple object with attributes used later in response construction
                            u = type('U', (), {})()
                            try:
                                # Row may be mapping-like or tuple-like depending on DB driver
                                u.id = rw['id'] if 'id' in rw.keys() else rw[0]
                                u.email = rw['email'] if 'email' in rw.keys() else (rw[1] if len(rw) > 1 else None)
                                u.nombre = rw['nombre'] if 'nombre' in rw.keys() else (rw[2] if len(rw) > 2 else None)
                                u.creado_en = rw['creado_en'] if 'creado_en' in rw.keys() else None
                                u.activo = rw['activo'] if 'activo' in rw.keys() else True
                                u._role_fallback = rw['role'] if 'role' in rw.keys() else 'usuario'
                            except Exception:
                                # Safe fallback for unexpected row shapes
                                try:
                                    u.id = rw[0]
                                except Exception:
                                    u.id = None
                                u.email = None
                                u.nombre = None
                                u.creado_en = None
                                u.activo = True
                                u._role_fallback = 'usuario'
                            users.append(u)
                    except Exception:
                        # If even the fallback fails, re-raise the original error so it is logged and surfaced.
                        raise
            except Exception:
                # Re-raise the original for outer handler
                raise
        ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@test.local')
        result = []
        for u in users:
            if u.email == ADMIN_EMAIL:
                urole = 'admin'
            elif getattr(u, 'entrenador', None):
                urole = 'entrenador'
            elif getattr(u, 'cliente', None):
                urole = 'cliente'
            else:
                urole = 'usuario'
            result.append({'id': u.id, 'email': u.email, 'nombre': u.nombre, 'creado_en': u.creado_en.isoformat(), 'role': urole, 'activo': getattr(u, 'activo', True)})
        return jsonify(result), 200
    except Exception as e:
        app.logger.exception('admin_list_users failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/admin/entrenadores/aceptados', methods=['GET'])
@jwt_required
def admin_entrenadores_aceptados():
    """Devuelve para cada entrenador sus rutinas y planes con:
    - cuántas solicitudes fueron aceptadas (estado=='aceptado')
    - lista de clientes que tienen la solicitud aceptada
    - para rutinas también se incluye cuántos clientes la tienen guardada (cliente_rutina)
    Endpoint protegido: admin only
    """
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    try:
        from database.database import Entrenador, Rutina, PlanAlimenticio, SolicitudPlan, Cliente, Usuario
        result = []
        entrenadores = Entrenador.query.all()
        for ent in entrenadores:
            ent_obj = {'entrenador_id': ent.id, 'usuario_id': getattr(ent, 'usuario_id', None), 'nombre': None, 'rutinas': [], 'planes': []}
            try:
                if getattr(ent, 'usuario', None):
                    ent_obj['nombre'] = getattr(ent.usuario, 'nombre', None)
            except Exception:
                ent_obj['nombre'] = None

            # Rutinas
            try:
                rutinas = Rutina.query.filter_by(entrenador_id=ent.id).order_by(Rutina.creado_en.desc()).all()
            except Exception:
                rutinas = []

            for r in rutinas:
                # accepted solicitudes for this rutina
                try:
                    accepted_sols = SolicitudPlan.query.filter_by(rutina_id=r.id, estado='aceptado').all()
                except Exception:
                    accepted_sols = []

                accepted_clients = []
                for s in accepted_sols:
                    try:
                        c = Cliente.query.filter_by(id=s.cliente_id).first()
                        if c:
                            u = Usuario.query.filter_by(id=getattr(c, 'usuario_id', None)).first()
                            accepted_clients.append({'cliente_id': c.id, 'usuario_id': getattr(u, 'id', None) if u else None, 'nombre': getattr(u, 'nombre', None) if u else None})
                    except Exception:
                        pass

                # count how many clientes have saved/followed this rutina (cliente_rutina table)
                try:
                    row = db.session.execute(text('SELECT COUNT(*) as cnt FROM cliente_rutina WHERE rutina_id = :rid'), {'rid': r.id}).fetchone()
                    saved_count = int(row['cnt'] if row and 'cnt' in row.keys() else (row[0] if row else 0))
                except Exception:
                    saved_count = 0

                # list of users who saved via cliente_rutina
                saved_users = []
                try:
                    rows = db.session.execute(text('SELECT cr.cliente_id AS cliente_id, u.id AS usuario_id, u.nombre AS nombre FROM cliente_rutina cr JOIN clientes c ON cr.cliente_id = c.id JOIN usuarios u ON c.usuario_id = u.id WHERE cr.rutina_id = :rid'), {'rid': r.id}).fetchall()
                    for rw in rows:
                        try:
                            saved_users.append({'cliente_id': rw['cliente_id'], 'usuario_id': rw['usuario_id'], 'nombre': rw['nombre']})
                        except Exception:
                            # fallback for tuple-like rows
                            try:
                                saved_users.append({'cliente_id': rw[0], 'usuario_id': rw[1], 'nombre': rw[2]})
                            except Exception:
                                pass
                except Exception:
                    saved_users = []

                ent_obj['rutinas'].append({'id': r.id, 'nombre': r.nombre, 'accepted_count': len(accepted_sols), 'accepted_clients': accepted_clients, 'saved_count': saved_count, 'saved_users': saved_users, 'link_url': getattr(r, 'link_url', None)})

            # Planes
            try:
                planes = PlanAlimenticio.query.filter_by(entrenador_id=ent.id).order_by(PlanAlimenticio.creado_en.desc()).all()
            except Exception:
                planes = []

            for p in planes:
                try:
                    accepted_sols = SolicitudPlan.query.filter_by(plan_id=p.id, estado='aceptado').all()
                except Exception:
                    accepted_sols = []
                accepted_clients = []
                for s in accepted_sols:
                    try:
                        c = Cliente.query.filter_by(id=s.cliente_id).first()
                        if c:
                            u = Usuario.query.filter_by(id=getattr(c, 'usuario_id', None)).first()
                            accepted_clients.append({'cliente_id': c.id, 'usuario_id': getattr(u, 'id', None) if u else None, 'nombre': getattr(u, 'nombre', None) if u else None})
                    except Exception:
                        pass

                # For plans we don't have a cliente_plan join table; use accepted solicitudes as proxy for 'seleccionada'
                ent_obj['planes'].append({'id': p.id, 'nombre': p.nombre, 'accepted_count': len(accepted_sols), 'accepted_clients': accepted_clients})

            result.append(ent_obj)

        return jsonify(result), 200
    except Exception as e:
        app.logger.exception('admin_entrenadores_aceptados failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/admin/usuarios/<int:usuario_id>/promote', methods=['POST'])
@jwt_required
def admin_promote_usuario(usuario_id):
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    try:
        from database.database import Usuario, Entrenador
        user = Usuario.query.filter_by(id=usuario_id).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404
        existing = Entrenador.query.filter_by(usuario_id=user.id).first()
        if existing:
            return jsonify({'message': 'already entrenador', 'entrenador_id': existing.id}), 200
        entrenador = Entrenador(usuario_id=user.id)
        db.session.add(entrenador)
        db.session.commit()
        return jsonify({'message': 'promoted to entrenador', 'entrenador_id': entrenador.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/admin/usuarios/<int:usuario_id>', methods=['DELETE'])
@jwt_required
def admin_delete_usuario(usuario_id):
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403
    # Support two modes:
    # - soft (default): mark the Usuario.activo = False and unpublish the entrenador's content
    # - hard: fully remove the user and related entrenador/cliente/planes/rutinas
    mode = (request.args.get('mode') or '').lower()
    try:
        from database.database import Usuario, Cliente, Entrenador, PlanAlimenticio, Rutina, SolicitudPlan
        user = Usuario.query.filter_by(id=usuario_id).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404

        # Hard delete: remove user and all owned content
        if mode == 'hard':
            try:
                # delete entrenador-owned content if exists
                entrenador = Entrenador.query.filter_by(usuario_id=user.id).first()
                if entrenador:
                    # delete solicitudes referencing plans or rutinas owned by this entrenador
                    try:
                        # delete solicitudes referencing plans
                        plan_ids = [p.id for p in PlanAlimenticio.query.filter_by(entrenador_id=entrenador.id).all()]
                        if plan_ids:
                            SolicitudPlan.query.filter(SolicitudPlan.plan_id.in_(plan_ids)).delete(synchronize_session=False)
                    except Exception:
                        db.session.rollback()
                    try:
                        # delete solicitudes referencing rutinas
                        rutina_ids = [r.id for r in Rutina.query.filter_by(entrenador_id=entrenador.id).all()]
                        if rutina_ids:
                            SolicitudPlan.query.filter(SolicitudPlan.rutina_id.in_(rutina_ids)).delete(synchronize_session=False)
                    except Exception:
                        db.session.rollback()
                    # delete planes and rutinas
                    try:
                        PlanAlimenticio.query.filter_by(entrenador_id=entrenador.id).delete()
                        Rutina.query.filter_by(entrenador_id=entrenador.id).delete()
                    except Exception:
                        db.session.rollback()
                    # delete entrenador row
                    try:
                        Entrenador.query.filter_by(usuario_id=user.id).delete()
                    except Exception:
                        db.session.rollback()

                # delete cliente row if exists
                try:
                    Cliente.query.filter_by(usuario_id=user.id).delete()
                except Exception:
                    db.session.rollback()

                # finally delete the user
                db.session.delete(user)
                db.session.commit()
                return jsonify({'message': 'usuario eliminado (hard)'}), 200
            except Exception as e:
                db.session.rollback()
                app.logger.exception('admin_delete_usuario hard delete failed')
                return jsonify({'error': 'db error', 'detail': str(e)}), 500

        # Soft delete (default): mark user inactive and unpublish their content so customers don't see it
        try:
            user.activo = False
            # Unpublish entrenador content if present
            entrenador = Entrenador.query.filter_by(usuario_id=user.id).first()
            if entrenador:
                try:
                    Rutina.query.filter_by(entrenador_id=entrenador.id).update({'es_publica': False})
                except Exception:
                    db.session.rollback()
                try:
                    PlanAlimenticio.query.filter_by(entrenador_id=entrenador.id).update({'es_publico': False})
                except Exception:
                    db.session.rollback()

            db.session.add(user)
            db.session.commit()
            return jsonify({'message': 'usuario desactivado (soft), contenido no público'}), 200
        except Exception as e:
            db.session.rollback()
            app.logger.exception('admin_delete_usuario soft disable failed')
            return jsonify({'error': 'db error', 'detail': str(e)}), 500
    except Exception as e:
        app.logger.exception('admin_delete_usuario: unexpected error')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/admin/usuarios/<int:usuario_id>/create_cliente', methods=['POST'])
@jwt_required
def admin_create_cliente(usuario_id):
    """Crea una fila Cliente para el usuario dado si no existe.

    Endpoint protegido: solo role == 'admin'. Útil para provisionar clientes
    en producción cuando el seed no creó la fila cliente.
    """
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    try:
        from database.database import Usuario, Cliente
        user = Usuario.query.filter_by(id=usuario_id).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404

        existing = Cliente.query.filter_by(usuario_id=user.id).first()
        if existing:
            return jsonify({'message': 'cliente already exists', 'cliente_id': existing.id}), 200

        cliente = Cliente(usuario_id=user.id)
        db.session.add(cliente)
        db.session.commit()
        return jsonify({'message': 'cliente creado', 'cliente_id': cliente.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


# Allow preflight OPTIONS for reactivate without auth so browsers can perform the CORS preflight.
@app.route('/api/admin/usuarios/<int:usuario_id>/reactivar', methods=['OPTIONS'])
def admin_reactivar_options(usuario_id):
    # flask-cors will attach the proper CORS headers; return 200 OK to satisfy preflight.
    return ('', 200)


@app.route('/api/admin/usuarios/<int:usuario_id>/reactivar', methods=['POST'])
@jwt_required
def admin_reactivar_usuario(usuario_id):
    """Reactivar (marcar activo) a un usuario previamente desactivado.

    Endpoint protegido: solo role == 'admin'. No re-publica automáticamente el contenido
    del entrenador (para evitar cambios inesperados); sólo marca `activo = True`.
    """
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    try:
        from database.database import Usuario
        user = Usuario.query.filter_by(id=usuario_id).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404

        try:
            user.activo = True
            db.session.add(user)
            db.session.commit()
            return jsonify({'message': 'usuario reactivado'}), 200
        except Exception as e:
            db.session.rollback()
            app.logger.exception('admin_reactivar_usuario failed')
            return jsonify({'error': 'db error', 'detail': str(e)}), 500
    except Exception as e:
        app.logger.exception('admin_reactivar_usuario: unexpected error')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/admin/usuarios/<int:usuario_id>/set_role', methods=['POST'])
@jwt_required
def admin_set_user_role(usuario_id):
    """Permite al admin cambiar el rol de un usuario a 'cliente', 'entrenador' o 'usuario'.

    - 'entrenador': crea una fila Entrenador si no existe.
    - 'cliente': crea una fila Cliente si no existe y elimina Entrenador si existe.
    - 'usuario': elimina filas Cliente y Entrenador (dejando solo Usuario).
    """
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    data = request.get_json() or {}
    desired = (data.get('role') or '').strip().lower()
    if desired not in ('cliente', 'entrenador', 'usuario'):
        return jsonify({'error': 'invalid role'}), 400

    try:
        from database.database import Usuario, Cliente, Entrenador
        user = Usuario.query.filter_by(id=usuario_id).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404

        # Switch behaviour
        if desired == 'entrenador':
            existing = Entrenador.query.filter_by(usuario_id=user.id).first()
            if existing:
                return jsonify({'message': 'already entrenador'}), 200
            # create entrenador row
            ent = Entrenador(usuario_id=user.id)
            db.session.add(ent)
            try:
                db.session.commit()
                return jsonify({'message': 'usuario promovido a entrenador'}), 201
            except Exception as e:
                db.session.rollback()
                app.logger.exception('admin_set_user_role: failed creating entrenador')
                return jsonify({'error': 'db error', 'detail': str(e)}), 500

        if desired == 'cliente':
            # ensure cliente exists
            existing_c = Cliente.query.filter_by(usuario_id=user.id).first()
            if not existing_c:
                try:
                    c = Cliente(usuario_id=user.id)
                    db.session.add(c)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    app.logger.exception('admin_set_user_role: failed creating cliente')
                    return jsonify({'error': 'db error', 'detail': str(e)}), 500
            # remove entrenador if exists
            try:
                Entrenador.query.filter_by(usuario_id=user.id).delete()
                db.session.commit()
            except Exception:
                db.session.rollback()
            return jsonify({'message': 'usuario establecido como cliente (entrenador eliminado si existía)'}), 200

        if desired == 'usuario':
            # remove both relations
            try:
                Entrenador.query.filter_by(usuario_id=user.id).delete()
                Cliente.query.filter_by(usuario_id=user.id).delete()
                db.session.commit()
                return jsonify({'message': 'usuario convertido a usuario simple (sin roles)'}), 200
            except Exception as e:
                db.session.rollback()
                app.logger.exception('admin_set_user_role: failed removing roles')
                return jsonify({'error': 'db error', 'detail': str(e)}), 500

    except Exception as e:
        app.logger.exception('admin_set_user_role: unexpected error')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


# Entrenador: listar mis rutinas/planes con clientes cuya solicitud fue aceptada
@app.route('/api/entrenador/aceptados', methods=['GET'])
@jwt_required
def entrenador_aceptados():
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    try:
        entrenador = Entrenador.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        entrenador = None
    if not entrenador:
        return jsonify({'error': 'forbidden: not entrenador'}), 403

    try:
        from database.database import Rutina, PlanAlimenticio, SolicitudPlan, Cliente, Usuario
        result = {'rutinas': [], 'planes': []}

        # Rutinas del entrenador
        try:
            rutinas = Rutina.query.filter_by(entrenador_id=entrenador.id).order_by(Rutina.creado_en.desc()).all()
        except Exception:
            rutinas = []

        for r in rutinas:
            try:
                accepted_sols = SolicitudPlan.query.filter_by(rutina_id=r.id, estado='aceptado').all()
            except Exception:
                accepted_sols = []
            accepted_clients = []
            for s in accepted_sols:
                try:
                    c = Cliente.query.filter_by(id=s.cliente_id).first()
                    u = Usuario.query.filter_by(id=getattr(c, 'usuario_id', None)).first() if c else None
                    accepted_clients.append({'cliente_id': c.id if c else None, 'usuario_id': getattr(u, 'id', None) if u else None, 'nombre': getattr(u, 'nombre', None) if u else None})
                except Exception:
                    pass

            # saved count from cliente_rutina
            try:
                row = db.session.execute(text('SELECT COUNT(*) as cnt FROM cliente_rutina WHERE rutina_id = :rid'), {'rid': r.id}).fetchone()
                saved_count = int(row['cnt'] if row and 'cnt' in row.keys() else (row[0] if row else 0))
            except Exception:
                saved_count = 0

            result['rutinas'].append({'id': r.id, 'nombre': r.nombre, 'accepted_count': len(accepted_sols), 'accepted_clients': accepted_clients, 'saved_count': saved_count, 'link_url': getattr(r, 'link_url', None)})

        # Planes del entrenador
        try:
            planes = PlanAlimenticio.query.filter_by(entrenador_id=entrenador.id).order_by(PlanAlimenticio.creado_en.desc()).all()
        except Exception:
            planes = []

        for p in planes:
            try:
                accepted_sols = SolicitudPlan.query.filter_by(plan_id=p.id, estado='aceptado').all()
            except Exception:
                accepted_sols = []
            accepted_clients = []
            for s in accepted_sols:
                try:
                    c = Cliente.query.filter_by(id=s.cliente_id).first()
                    u = Usuario.query.filter_by(id=getattr(c, 'usuario_id', None)).first() if c else None
                    accepted_clients.append({'cliente_id': c.id if c else None, 'usuario_id': getattr(u, 'id', None) if u else None, 'nombre': getattr(u, 'nombre', None) if u else None})
                except Exception:
                    pass

            result['planes'].append({'id': p.id, 'nombre': p.nombre, 'accepted_count': len(accepted_sols), 'accepted_clients': accepted_clients})

        return jsonify(result), 200
    except Exception as e:
        app.logger.exception('entrenador_aceptados failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/usuarios/<int:usuario_id>', methods=['GET'])
@jwt_required
def obtener_usuario_perfil(usuario_id):
    """Devuelve el perfil público/administrativo de un usuario.

    - Admins pueden ver cualquier usuario.
    - Usuarios normales solo pueden ver su propio perfil.
    """
    token_user_id = request.jwt_payload.get('user_id')
    token_role = request.jwt_payload.get('role')
    # allow admin or owner
    if token_role != 'admin' and token_user_id != usuario_id:
        return jsonify({'error': 'forbidden: can only view own profile'}), 403

    try:
        from database.database import Usuario, Cliente, Entrenador, Rutina
        user = Usuario.query.filter_by(id=usuario_id).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404

        # determine roles
        is_admin = (user.email == os.getenv('ADMIN_EMAIL', 'admin@test.local'))
        has_entrenador = True if Entrenador.query.filter_by(usuario_id=user.id).first() else False
        has_cliente = True if Cliente.query.filter_by(usuario_id=user.id).first() else False

        perfil = {
            'id': user.id,
            'email': user.email,
            'nombre': user.nombre,
            'activo': getattr(user, 'activo', True),
            'creado_en': user.creado_en.isoformat() if getattr(user, 'creado_en', None) else None,
            'roles': []
        }
        if is_admin:
            perfil['roles'].append('admin')
        if has_entrenador:
            perfil['roles'].append('entrenador')
        if has_cliente:
            perfil['roles'].append('cliente')

        # include entrenador details (if any)
        if has_entrenador:
            ent = Entrenador.query.filter_by(usuario_id=user.id).first()
            perfil['entrenador'] = {'id': ent.id, 'speciality': getattr(ent, 'speciality', None)}
            # include simple list of rutinas
            try:
                rutinas = Rutina.query.filter_by(entrenador_id=ent.id).order_by(Rutina.creado_en.desc()).limit(20).all()
                perfil['rutinas'] = [{'id': r.id, 'nombre': r.nombre} for r in rutinas]
            except Exception:
                perfil['rutinas'] = []

        # include cliente details
        if has_cliente:
            cli = Cliente.query.filter_by(usuario_id=user.id).first()
            perfil['cliente'] = {'id': cli.id, 'edad': getattr(cli, 'edad', None), 'peso': getattr(cli, 'peso', None), 'altura': getattr(cli, 'altura', None)}

        return jsonify(perfil), 200
    except Exception as e:
        app.logger.exception('obtener_usuario_perfil failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/usuarios/logout', methods=['POST'])
@jwt_required
def logout_usuario():
    """Invalidate current JWT by storing its `jti` in `revoked_tokens`.
    The frontend should call this on logout to ensure server-side revocation.
    """
    payload = request.jwt_payload or {}
    jti = payload.get('jti')
    if not jti:
        return jsonify({'error': 'token has no jti, cannot revoke'}), 400
    try:
        from database.database import RevokedToken
        revoked = RevokedToken(jti=jti)
        db.session.add(revoked)
        db.session.commit()
        return jsonify({'message': 'token revoked'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('logout failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/entrenador/perfil', methods=['GET'])
@jwt_required
def get_entrenador_perfil():
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401
    try:
        from database.database import Entrenador, Usuario
        ent = Entrenador.query.filter_by(usuario_id=token_user_id).first()
        if not ent:
            return jsonify({'error': 'entrenador not found'}), 404
        user = Usuario.query.filter_by(id=token_user_id).first()
        perfil = {
            'usuario_id': token_user_id,
            'nombre': getattr(user, 'nombre', None),
            'email': getattr(user, 'email', None),
            'speciality': getattr(ent, 'speciality', None),
            'bio': getattr(ent, 'bio', None),
            'telefono': getattr(ent, 'telefono', None),
            'instagram_url': getattr(ent, 'instagram_url', None),
            'youtube_url': getattr(ent, 'youtube_url', None),
            'id': ent.id
        }
        return jsonify(perfil), 200
    except Exception as e:
        app.logger.exception('get_entrenador_perfil failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/entrenador/perfil', methods=['PUT'])
@jwt_required
def update_entrenador_perfil():
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401
    data = request.get_json() or {}
    try:
        from database.database import Entrenador
        ent = Entrenador.query.filter_by(usuario_id=token_user_id).first()
        if not ent:
            return jsonify({'error': 'entrenador not found'}), 404
        # Accept fields: speciality, bio, telefono
        if 'speciality' in data:
            ent.speciality = data.get('speciality')
        if 'bio' in data:
            ent.bio = data.get('bio')
        if 'telefono' in data:
            ent.telefono = data.get('telefono')
        if 'instagram_url' in data:
            # Basic acceptance of instagram url (no validation here)
            ent.instagram_url = data.get('instagram_url')
        if 'youtube_url' in data:
            ent.youtube_url = data.get('youtube_url')
        db.session.add(ent)
        db.session.commit()
        return jsonify({'message': 'perfil actualizado'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('update_entrenador_perfil failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/entrenadores', methods=['GET'])
def listar_entrenadores_publicos():
    """Listado público de entrenadores activos. Devuelve usuarios que tienen
    una fila Entrenador y cuyo Usuario.activo != False.
    """
    try:
        from database.database import Entrenador, Usuario
        trainers = []
        try:
            ents = Entrenador.query.order_by(Entrenador.id.desc()).all()
        except Exception:
            ents = []

        for ent in ents:
            try:
                user = Usuario.query.filter_by(id=getattr(ent, 'usuario_id', None)).first()
                if not user:
                    continue
                if getattr(user, 'activo', True) is False:
                    continue
                trainers.append({'usuario_id': user.id, 'nombre': getattr(user, 'nombre', None), 'speciality': getattr(ent, 'speciality', None), 'bio': getattr(ent, 'bio', None), 'telefono': getattr(ent, 'telefono', None), 'instagram_url': getattr(ent, 'instagram_url', None), 'youtube_url': getattr(ent, 'youtube_url', None), 'entrenador_id': ent.id})
            except Exception:
                # skip malformed rows
                continue

        return jsonify(trainers), 200
    except Exception as e:
        # Don't break the client UI: log the error but return an empty list so
        # the client can still render the page. This favors availability for
        # the public trainers list even when the DB has schema issues.
        app.logger.exception('listar_entrenadores_publicos failed; returning empty list to preserve UX')
        return jsonify([]), 200


@app.route('/api/entrenadores', methods=['OPTIONS'])
def listar_entrenadores_publicos_options():
    # Allow CORS preflight to succeed with 200 and proper headers (flask-cors will attach headers).
    return ('', 200)


# Backwards-compatible, ultra-safe public endpoints under /api/public/*
# These always return safe JSON (empty lists or 404) and avoid any complex DB logic
# so the frontend can rely on them even if more advanced handlers fail.
@app.route('/api/public/entrenadores', methods=['GET', 'OPTIONS'])
def public_list_entrenadores():

    if request.method == 'OPTIONS':
        return ('', 200)
    try:
        from database.database import Entrenador, Usuario
        trainers = []
        try:
            ents = Entrenador.query.order_by(Entrenador.id.desc()).all()
        except Exception:
            ents = []
        ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@test.local')
        for ent in ents:
            try:
                user = Usuario.query.filter_by(id=getattr(ent, 'usuario_id', None)).first()
                if not user or getattr(user, 'activo', True) is False:
                    continue
                # Exclude the configured admin account from public trainer listings
                if getattr(user, 'email', None) and getattr(user, 'email') == ADMIN_EMAIL:
                    continue
                trainers.append({'usuario_id': user.id, 'nombre': getattr(user, 'nombre', None), 'speciality': getattr(ent, 'speciality', None), 'bio': getattr(ent, 'bio', None), 'telefono': getattr(ent, 'telefono', None), 'instagram_url': getattr(ent, 'instagram_url', None), 'youtube_url': getattr(ent, 'youtube_url', None)})
            except Exception:
                continue
        return jsonify(trainers), 200
    except Exception as e:
        # Log full exception and return diagnostic info in development to help
        # identify the root cause. This will be visible in the frontend JSON
        # when a 500 occurs so you can paste it here for debugging.
        app.logger.exception('public_list_entrenadores failed')
        # Return error details in development (not for production)
        is_prod = bool(os.getenv('DATABASE_URL'))
        if is_prod:
            return jsonify({'error': 'internal'}), 500
        else:
            return jsonify({'error': 'internal', 'type': e.__class__.__name__, 'detail': str(e)}), 500


@app.route('/api/public/entrenadores/<int:usuario_id>', methods=['GET', 'OPTIONS'])
def public_get_entrenador(usuario_id):
    if request.method == 'OPTIONS':
        return ('', 200)
    try:
        from database.database import Usuario, Entrenador, Rutina, PlanAlimenticio
        user = Usuario.query.filter_by(id=usuario_id).first()
        if not user:
            return jsonify({'error': 'not found'}), 404
        ent = Entrenador.query.filter_by(usuario_id=user.id).first()
        if not ent:
            return jsonify({'error': 'not found'}), 404
        if getattr(user, 'activo', True) is False:
            return jsonify({'error': 'not found'}), 404
        perfil = {
            'usuario_id': user.id,
            'nombre': user.nombre,
            'email': getattr(user, 'email', None),
            'speciality': getattr(ent, 'speciality', None),
            'bio': getattr(ent, 'bio', None),
            'instagram_url': getattr(ent, 'instagram_url', None),
            'youtube_url': getattr(ent, 'youtube_url', None),
            'telefono': getattr(ent, 'telefono', None),
            'rutinas': [],
            'planes': []
        }
        try:
            ruts = Rutina.query.filter_by(entrenador_id=ent.id, es_publica=True).order_by(Rutina.creado_en.desc()).all()
            for r in ruts:
                perfil['rutinas'].append({'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion, 'nivel': r.nivel, 'link_url': getattr(r, 'link_url', None)})
        except Exception:
            perfil['rutinas'] = []
        try:
            planes = PlanAlimenticio.query.filter_by(entrenador_id=ent.id, es_publico=True).order_by(PlanAlimenticio.creado_en.desc()).all()
            for p in planes:
                perfil['planes'].append({'id': p.id, 'nombre': p.nombre, 'descripcion': p.descripcion})
        except Exception:
            perfil['planes'] = []
        return jsonify(perfil), 200
    except Exception as e:
        app.logger.exception('public_get_entrenador failed')
        is_prod = bool(os.getenv('DATABASE_URL'))
        if is_prod:
            return jsonify({'error': 'internal'}), 500
        else:
            return jsonify({'error': 'internal', 'type': e.__class__.__name__, 'detail': str(e)}), 500


@app.route('/api/entrenadores/<int:usuario_id>', methods=['GET'])
def obtener_entrenador_publico(usuario_id):
    """Devuelve el perfil público de un entrenador (por usuario.id) incluyendo
    sus rutinas públicas y planes públicos. Público: no requiere autenticación.
    """
    try:
        from database.database import Usuario, Entrenador, Rutina, PlanAlimenticio

        user = Usuario.query.filter_by(id=usuario_id).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404
        # must be an entrenador
        ent = Entrenador.query.filter_by(usuario_id=user.id).first()
        if not ent:
            return jsonify({'error': 'entrenador not found'}), 404
        # if user deactivated, respond 404 to hide profile
        if getattr(user, 'activo', True) is False:
            return jsonify({'error': 'entrenador not found'}), 404

        perfil = {
            'usuario_id': user.id,
            'nombre': user.nombre,
            'email': getattr(user, 'email', None),
            'speciality': getattr(ent, 'speciality', None),
            'bio': getattr(ent, 'bio', None),
            'instagram_url': getattr(ent, 'instagram_url', None),
            'youtube_url': getattr(ent, 'youtube_url', None),
            'telefono': getattr(ent, 'telefono', None),
            'entrenador_id': ent.id,
            'rutinas': [],
            'planes': []
        }

        # rutinas públicas del entrenador
        try:
            ruts = Rutina.query.filter_by(entrenador_id=ent.id, es_publica=True).order_by(Rutina.creado_en.desc()).all()
            for r in ruts:
                perfil['rutinas'].append({'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion, 'nivel': r.nivel, 'creado_en': getattr(r.creado_en, 'isoformat', lambda: None)() if getattr(r, 'creado_en', None) else None, 'link_url': getattr(r, 'link_url', None)})
        except Exception:
            perfil['rutinas'] = []

        # planes públicos del entrenador
        try:
            planes = PlanAlimenticio.query.filter_by(entrenador_id=ent.id, es_publico=True).order_by(PlanAlimenticio.creado_en.desc()).all()
            for p in planes:
                perfil['planes'].append({'id': p.id, 'nombre': p.nombre, 'descripcion': p.descripcion, 'creado_en': getattr(p.creado_en, 'isoformat', lambda: None)() if getattr(p, 'creado_en', None) else None})
        except Exception:
            perfil['planes'] = []

        return jsonify(perfil), 200
    except Exception as e:
        app.logger.exception('obtener_entrenador_publico failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/entrenadores/<int:usuario_id>', methods=['OPTIONS'])
def obtener_entrenador_publico_options(usuario_id):
    # Allow CORS preflight to succeed for trainer profile endpoint.
    return ('', 200)


@app.route('/api/admin/metrics', methods=['GET'])
@jwt_required
def admin_metrics():
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    # Make metrics resilient: count each table separately and don't return 500
    # Compute clearer metrics and disambiguate user roles.
    # Definitions returned:
    # - total_users: number of Usuario rows
    # - total_clientes: number of distinct usuarios that have a Cliente row
    # - total_entrenadores: number of distinct usuarios that have an Entrenador row
    # - both_roles: usuarios that appear as both Cliente and Entrenador
    # - clientes_only / entrenadores_only: derived counts
    try:
        from database.database import Usuario, Cliente, Entrenador, Medicion, Rutina
        from sqlalchemy import func

        # total usuarios
        total_users = db.session.query(func.count(Usuario.id)).scalar() or 0

        # distinct usuario counts in Cliente and Entrenador
        total_client_user_count = db.session.query(func.count(func.distinct(Cliente.usuario_id))).scalar() or 0
        total_entrenador_user_count = db.session.query(func.count(func.distinct(Entrenador.usuario_id))).scalar() or 0

        # users that have both cliente AND entrenador
        both_count = db.session.query(func.count(func.distinct(Usuario.id))).join(Cliente, Cliente.usuario_id == Usuario.id).join(Entrenador, Entrenador.usuario_id == Usuario.id).scalar() or 0

        clientes_only = max(0, int(total_client_user_count) - int(both_count))
        entrenadores_only = max(0, int(total_entrenador_user_count) - int(both_count))

        result = {
            'total_users': int(total_users),
            'total_clientes': int(total_client_user_count),
            'total_entrenadores': int(total_entrenador_user_count),
            'both_roles': int(both_count),
            'clientes_only': int(clientes_only),
            'entrenadores_only': int(entrenadores_only)
        }

        return jsonify(result), 200
    except Exception as e:
        app.logger.exception('admin_metrics: failed computing metrics')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500



@app.route('/api/admin/review', methods=['GET'])
@jwt_required
def admin_review_list():
        """Devuelve rutinas y planes no publicados para que el admin los revise."""
        role = request.jwt_payload.get('role')
        if role != 'admin':
            return jsonify({'error': 'forbidden: admin only'}), 403

        try:
            from database.database import Rutina, PlanAlimenticio, Entrenador, Usuario, ContentReview
            # Prefer explicit ContentReview rows when available (tracks pending items)
            try:
                pending = ContentReview.query.filter_by(estado='pendiente').order_by(ContentReview.creado_en.desc()).all()
            except Exception:
                pending = []
            # Build lists from pending reviews if present, otherwise fallback to checking es_publica/es_publico flags
            rutinas = []
            planes = []
            if pending:
                for rev in pending:
                    if rev.tipo == 'rutina':
                        r = Rutina.query.filter_by(id=rev.content_id).first()
                        if r:
                            rutinas.append(r)
                    elif rev.tipo == 'plan':
                        p = PlanAlimenticio.query.filter_by(id=rev.content_id).first()
                        if p:
                            planes.append(p)
                # If there were pending review rows but none map to existing content
                # (or mapping produced empty lists), fall back to listing non-public
                # rutinas/planes so the admin still sees items to review.
                if not rutinas and not planes:
                    rutinas = Rutina.query.filter_by(es_publica=False).order_by(Rutina.creado_en.desc()).all()
                    planes = PlanAlimenticio.query.filter_by(es_publico=False).order_by(PlanAlimenticio.creado_en.desc()).all()
            else:
                # No ContentReview rows at all: list non-public content
                rutinas = Rutina.query.filter_by(es_publica=False).order_by(Rutina.creado_en.desc()).all()
                planes = PlanAlimenticio.query.filter_by(es_publico=False).order_by(PlanAlimenticio.creado_en.desc()).all()

            rlist = []
            for r in rutinas:
                entrenador = Entrenador.query.filter_by(id=getattr(r, 'entrenador_id', None)).first()
                entrenador_usuario_id = getattr(entrenador, 'usuario_id', None) if entrenador else None
                entrenador_nombre = None
                try:
                    if entrenador_usuario_id:
                        u = Usuario.query.filter_by(id=entrenador_usuario_id).first()
                        if u:
                            entrenador_nombre = u.nombre
                except Exception:
                    entrenador_nombre = None
                rlist.append({'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion, 'nivel': r.nivel, 'entrenador_id': getattr(r, 'entrenador_id', None), 'entrenador_usuario_id': entrenador_usuario_id, 'entrenador_nombre': entrenador_nombre, 'creado_en': getattr(r, 'creado_en', None).isoformat() if getattr(r, 'creado_en', None) else None, 'link_url': getattr(r, 'link_url', None)})

            plist = []
            for p in planes:
                entrenador = Entrenador.query.filter_by(id=getattr(p, 'entrenador_id', None)).first()
                entrenador_usuario_id = getattr(entrenador, 'usuario_id', None) if entrenador else None
                entrenador_nombre = None
                try:
                    if entrenador_usuario_id:
                        u = Usuario.query.filter_by(id=entrenador_usuario_id).first()
                        if u:
                            entrenador_nombre = u.nombre
                except Exception:
                    entrenador_nombre = None
                plist.append({'id': p.id, 'nombre': p.nombre, 'descripcion': p.descripcion, 'contenido': p.contenido, 'entrenador_id': getattr(p, 'entrenador_id', None), 'entrenador_usuario_id': entrenador_usuario_id, 'entrenador_nombre': entrenador_nombre, 'creado_en': getattr(p, 'creado_en', None).isoformat() if getattr(p, 'creado_en', None) else None})

            return jsonify({'rutinas': rlist, 'planes': plist}), 200
        except Exception as e:
            app.logger.exception('admin_review_list failed')
            # In development show the exception detail to help debugging
            is_prod = bool(os.getenv('DATABASE_URL'))
            if not is_prod:
                return jsonify({'error': 'db error', 'detail': str(e)}), 500
            return jsonify({'error': 'db error'}), 500


    # Development helper: return pending review items without auth when running locally.
    # This helps debugging CORS/auth issues during development. Disabled in production.
@app.route('/api/admin/review/debug', methods=['GET'])
def admin_review_list_debug():
        if bool(os.getenv('DATABASE_URL')):
            return jsonify({'error': 'not available in production'}), 404
        try:
            from database.database import Rutina, PlanAlimenticio, Entrenador, Usuario
            rutinas = Rutina.query.filter_by(es_publica=False).order_by(Rutina.creado_en.desc()).all()
            planes = PlanAlimenticio.query.filter_by(es_publico=False).order_by(PlanAlimenticio.creado_en.desc()).all()
            rlist = []
            for r in rutinas:
                entrenador = Entrenador.query.filter_by(id=getattr(r, 'entrenador_id', None)).first()
                entrenador_usuario_id = getattr(entrenador, 'usuario_id', None) if entrenador else None
                entrenador_nombre = None
                try:
                    if entrenador_usuario_id:
                        u = Usuario.query.filter_by(id=entrenador_usuario_id).first()
                        if u:
                            entrenador_nombre = u.nombre
                except Exception:
                    entrenador_nombre = None
                rlist.append({'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion, 'nivel': r.nivel, 'entrenador_id': getattr(r, 'entrenador_id', None), 'entrenador_usuario_id': entrenador_usuario_id, 'entrenador_nombre': entrenador_nombre, 'creado_en': getattr(r, 'creado_en', None).isoformat() if getattr(r, 'creado_en', None) else None, 'link_url': getattr(r, 'link_url', None)})

            plist = []
            for p in planes:
                entrenador = Entrenador.query.filter_by(id=getattr(p, 'entrenador_id', None)).first()
                entrenador_usuario_id = getattr(entrenador, 'usuario_id', None) if entrenador else None
                entrenador_nombre = None
                try:
                    if entrenador_usuario_id:
                        u = Usuario.query.filter_by(id=entrenador_usuario_id).first()
                        if u:
                            entrenador_nombre = u.nombre
                except Exception:
                    entrenador_nombre = None
                plist.append({'id': p.id, 'nombre': p.nombre, 'descripcion': p.descripcion, 'contenido': p.contenido, 'entrenador_id': getattr(p, 'entrenador_id', None), 'entrenador_usuario_id': entrenador_usuario_id, 'entrenador_nombre': entrenador_nombre, 'creado_en': getattr(p, 'creado_en', None).isoformat() if getattr(p, 'creado_en', None) else None})

            return jsonify({'rutinas': rlist, 'planes': plist}), 200
        except Exception as e:
            app.logger.exception('admin_review_list_debug failed')
            return jsonify({'error': 'debug failed', 'detail': str(e)}), 500


@app.route('/api/debug/content_reviews', methods=['GET'])
def debug_content_reviews():
    # Dev-only: enumerate content_review rows to aid debugging local setups.
    if bool(os.getenv('DATABASE_URL')):
        return jsonify({'error': 'not available in production'}), 404
    try:
        from database.database import ContentReview, Usuario
        rows = ContentReview.query.order_by(ContentReview.creado_en.desc()).limit(200).all()
        out = []
        for r in rows:
            creador = None
            try:
                if getattr(r, 'creado_por', None):
                    u = Usuario.query.filter_by(id=r.creado_por).first()
                    if u:
                        creador = {'id': u.id, 'nombre': getattr(u, 'nombre', None), 'email': getattr(u, 'email', None)}
            except Exception:
                creador = None
            out.append({'id': r.id, 'tipo': r.tipo, 'content_id': r.content_id, 'estado': r.estado, 'creado_por': r.creado_por, 'creado_por_info': creador, 'creado_en': getattr(r, 'creado_en', None).isoformat() if getattr(r, 'creado_en', None) else None})
        return jsonify(out), 200
    except Exception as e:
        app.logger.exception('debug_content_reviews failed')
        return jsonify({'error': 'debug failed', 'detail': str(e)}), 500



@app.route('/api/admin/review/rutina/<int:rutina_id>/approve', methods=['POST'])
@jwt_required
def admin_approve_rutina(rutina_id):
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403
    try:
        from database.database import Rutina, ContentReview
        r = Rutina.query.filter_by(id=rutina_id).first()
        if not r:
            return jsonify({'error': 'rutina not found'}), 404

        # Update rutina and its ContentReview in a single transaction to avoid
        # partial commits. If ContentReview is missing, create one marked as accepted
        # for audit consistency.
        r.es_publica = True
        db.session.add(r)

        try:
            cr = ContentReview.query.filter_by(tipo='rutina', content_id=rutina_id).first()
        except Exception:
            cr = None

        if cr:
            cr.estado = 'aceptado'
            db.session.add(cr)
        else:
            try:
                new_cr = ContentReview(tipo='rutina', content_id=rutina_id, estado='aceptado', creado_por=request.jwt_payload.get('user_id'))
                db.session.add(new_cr)
            except Exception:
                # non-fatal: continue and commit rutina change even if creating review fails
                app.logger.exception('admin_approve_rutina: failed creating ContentReview')

        db.session.commit()
        return jsonify({'message': 'rutina publicada', 'id': r.id}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('admin_approve_rutina failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500



@app.route('/api/admin/review/rutina/<int:rutina_id>/reject', methods=['POST'])
@jwt_required
def admin_reject_rutina(rutina_id):
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403
    try:
        from database.database import Rutina
        r = Rutina.query.filter_by(id=rutina_id).first()
        if not r:
            return jsonify({'error': 'rutina not found'}), 404
        db.session.delete(r)
        db.session.commit()
        # Mark any related ContentReview as rejected
        try:
            from database.database import ContentReview
            cr = ContentReview.query.filter_by(tipo='rutina', content_id=rutina_id).first()
            if cr:
                cr.estado = 'rechazado'
                db.session.add(cr)
                db.session.commit()
        except Exception:
            db.session.rollback()
        return jsonify({'message': 'rutina rechazada y eliminada', 'id': rutina_id}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('admin_reject_rutina failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500



@app.route('/api/admin/review/plan/<int:plan_id>/approve', methods=['POST'])
@jwt_required
def admin_approve_plan(plan_id):
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403
    try:
        from database.database import PlanAlimenticio, ContentReview
        p = PlanAlimenticio.query.filter_by(id=plan_id).first()
        if not p:
            return jsonify({'error': 'plan not found'}), 404

        # Update plan and its ContentReview in one transaction. Create review if missing.
        p.es_publico = True
        db.session.add(p)

        try:
            cr = ContentReview.query.filter_by(tipo='plan', content_id=plan_id).first()
        except Exception:
            cr = None

        if cr:
            cr.estado = 'aceptado'
            db.session.add(cr)
        else:
            try:
                new_cr = ContentReview(tipo='plan', content_id=plan_id, estado='aceptado', creado_por=request.jwt_payload.get('user_id'))
                db.session.add(new_cr)
            except Exception:
                app.logger.exception('admin_approve_plan: failed creating ContentReview')

        db.session.commit()
        return jsonify({'message': 'plan publicado', 'id': p.id}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('admin_approve_plan failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500



@app.route('/api/admin/review/plan/<int:plan_id>/reject', methods=['POST'])
@jwt_required
def admin_reject_plan(plan_id):
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403
    try:
        from database.database import PlanAlimenticio
        p = PlanAlimenticio.query.filter_by(id=plan_id).first()
        if not p:
            return jsonify({'error': 'plan not found'}), 404
        db.session.delete(p)
        db.session.commit()
        # Mark review row rejected if exists
        try:
            from database.database import ContentReview
            cr = ContentReview.query.filter_by(tipo='plan', content_id=plan_id).first()
            if cr:
                cr.estado = 'rechazado'
                db.session.add(cr)
                db.session.commit()
        except Exception:
            db.session.rollback()
        return jsonify({'message': 'plan rechazado y eliminado', 'id': plan_id}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('admin_reject_plan failed')
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/admin/usuarios', methods=['POST'])
@jwt_required
def admin_create_user():
    """Crear un Usuario + relacione(s) en una sola transacción.

    Request JSON: { email, nombre, password, role }
    role: 'usuario' (default), 'cliente', 'entrenador'
    Solo admin puede ejecutar este endpoint.
    """
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    nombre = data.get('nombre') or email
    desired_role = data.get('role', 'usuario')

    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400

    try:
        from database.database import Usuario, Cliente, Entrenador

        existing = Usuario.query.filter_by(email=email).first()
        if existing:
            return jsonify({'error': 'user exists'}), 409

        hashed = generate_password_hash(password)
        user = Usuario(email=email, nombre=nombre, hashed_password=hashed)
        db.session.add(user)
        # flush so user.id is available for FK relations
        db.session.flush()

        # create relations according to desired_role
        created_rel = []
        if desired_role in ('cliente', 'usuario', 'admin'):
            try:
                cliente = Cliente(usuario_id=user.id)
                db.session.add(cliente)
                created_rel.append('cliente')
            except Exception:
                db.session.rollback()
                return jsonify({'error': 'failed creating cliente relation'}), 500
        if desired_role == 'entrenador':
            try:
                entrenador = Entrenador(usuario_id=user.id)
                db.session.add(entrenador)
                created_rel.append('entrenador')
            except Exception:
                db.session.rollback()
                return jsonify({'error': 'failed creating entrenador relation'}), 500

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'db error', 'detail': str(e)}), 500

        # determine role string for response
        ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@test.local')
        if user.email == ADMIN_EMAIL:
            resp_role = 'admin'
        elif 'entrenador' in created_rel:
            resp_role = 'entrenador'
        elif 'cliente' in created_rel:
            resp_role = 'cliente'
        else:
            resp_role = 'usuario'

        return jsonify({'message': 'user created', 'id': user.id, 'role': resp_role}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/admin/fix_schema', methods=['POST'])
@jwt_required
def admin_fix_schema():
    """Intenta arreglar problemas de esquema comunes en producción.

    - Ejecuta `db.create_all()` para crear tablas que falten.
    - Intenta añadir la columna `entrenador_id` en `rutinas` si falta.
    - Intenta añadir una FK simple hacia `entrenadores` (silenciosamente si ya existe).

    Este endpoint requiere role == 'admin'. Está pensado para uso puntual
    en despliegues donde la base de datos quedó desincronizada.
    """
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    try:
        with app.app_context():
            # crear tablas que falten (no altera tablas existentes)
            db.create_all()
            # añadir columna entrenador_id si no existe (Postgres supports IF NOT EXISTS)
            try:
                db.session.execute(text('ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS entrenador_id INTEGER'))
            except Exception:
                # ignore
                pass
            # intentar añadir constraint FK (si ya existe fallará y lo ignoramos)
            try:
                db.session.execute(text('ALTER TABLE rutinas ADD CONSTRAINT fk_rutinas_entrenador FOREIGN KEY (entrenador_id) REFERENCES entrenadores(id)'))
            except Exception:
                # ignore
                pass
            db.session.commit()
        return jsonify({'message': 'schema fix attempted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'schema fix failed', 'detail': str(e)}), 500


@app.route('/api/admin/fix_schema_v2', methods=['POST'])
@jwt_required
def admin_fix_schema_v2():
    """A stronger schema repair endpoint.

    - Verifies whether columna `entrenador_id` existe en `rutinas` using
      information_schema and adds it if missing. Also attempts to add FK.
    - Returns diagnostic info to help troubleshooting.
    """
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    try:
        with app.app_context():
            # Ensure tables exist
            db.create_all()

            # Get existing columns for 'rutinas'
            q_all = "SELECT column_name FROM information_schema.columns WHERE table_name='rutinas'"
            rows = db.session.execute(text(q_all)).fetchall()
            existing_cols = set([r[0] for r in rows])

            # Add entrenador_id and other expected columns for rutinas if missing
            expected = {
                'entrenador_id': "INTEGER",
                'cliente_id': "INTEGER",
                'nombre': "VARCHAR(200)",
                'descripcion': "TEXT",
                'nivel': "VARCHAR(50)",
                'es_publica': "BOOLEAN",
                'creado_en': "TIMESTAMP"
            }

            added = []
            errors = []
            for col, coltype in expected.items():
                check_q = f"SELECT column_name FROM information_schema.columns WHERE table_name='rutinas' AND column_name='{col}'"
                found = db.session.execute(text(check_q)).fetchone()
                if found:
                    continue
                # Compose ALTER for the column (use IF NOT EXISTS where supported)
                try:
                    alter_sql = f"ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS {col} {coltype}"
                    db.session.execute(text(alter_sql))
                    added.append(col)
                except Exception as e:
                    db.session.rollback()
                    errors.append({'column': col, 'error': str(e)})

                # Try to add FK for entrenador_id
            try:
                db.session.execute(text('ALTER TABLE rutinas ADD CONSTRAINT IF NOT EXISTS fk_rutinas_entrenador FOREIGN KEY (entrenador_id) REFERENCES entrenadores(id)'))
            except Exception:
                # not fatal
                pass

            # If cliente_id exists but is NOT NULL, try to make it nullable (Postgres)
            try:
                if 'cliente_id' in existing_cols:
                    try:
                        db.session.execute(text('ALTER TABLE rutinas ALTER COLUMN cliente_id DROP NOT NULL'))
                    except Exception:
                        # ignore if the DB doesn't support this or constraint not present
                        pass
            except Exception:
                pass

            # commit results
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': 'failed to commit column changes', 'detail': str(e), 'errors': errors}), 500

            # Report what happened
            if errors:
                return jsonify({'message': 'partial', 'added': added, 'errors': errors}), 200
            else:
                return jsonify({'message': 'columns ensured', 'added': added}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'schema fix v2 failed', 'detail': str(e)}), 500


@app.route('/api/admin/diagnose_rutinas', methods=['GET'])
@jwt_required
def admin_diagnose_rutinas():
    """Devuelve diagnóstico sobre la tabla `rutinas` y sus columnas.
    Útil para depurar problemas de esquema en producción.
    Requiere role == 'admin'.
    """
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    try:
        with app.app_context():
            # ¿Existe la tabla rutinas?
            q_table = "SELECT to_regclass('public.rutinas')"
            tbl = db.session.execute(text(q_table)).fetchone()
            table_exists = bool(tbl and tbl[0])

            # columnas existentes (Postgres information_schema)
            cols_q = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='rutinas'"
            cols = []
            try:
                rows = db.session.execute(text(cols_q)).fetchall()
                cols = [{'name': r[0], 'type': r[1]} for r in rows]
            except Exception:
                cols = []

            # row count (si existe)
            count = None
            if table_exists:
                try:
                    c = db.session.execute(text('SELECT COUNT(*) FROM rutinas')).fetchone()
                    count = int(c[0])
                except Exception:
                    count = None

            return jsonify({'table_exists': table_exists, 'row_count': count, 'columns': cols}), 200
    except Exception as e:
        app.logger.exception('admin_diagnose_rutinas failed')
        return jsonify({'error': 'diagnose failed', 'detail': str(e)}), 500


@app.route('/api/admin/repair_rutinas', methods=['POST'])
@jwt_required
def admin_repair_rutinas():
    """Intenta reparar la tabla rutinas: crear tabla si falta y añadir columnas esperadas.
    Requiere role == 'admin'. Devuelve un resumen de acciones realizadas.
    """
    role = request.jwt_payload.get('role')
    if role != 'admin':
        return jsonify({'error': 'forbidden: admin only'}), 403

    try:
        with app.app_context():
            db.create_all()
            expected = {
                'entrenador_id': "INTEGER",
                'nombre': "VARCHAR(200)",
                'descripcion': "TEXT",
                'nivel': "VARCHAR(50)",
                'es_publica': "BOOLEAN",
                'creado_en': "TIMESTAMP"
            }

            # also ensure cliente_id is present and nullable
            try:
                db.session.execute(text('ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS cliente_id INTEGER'))
                try:
                    db.session.execute(text('ALTER TABLE rutinas ALTER COLUMN cliente_id DROP NOT NULL'))
                except Exception:
                    pass
            except Exception:
                pass
            added = []
            errors = []
            for col, coltype in expected.items():
                try:
                    db.session.execute(text(f"ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS {col} {coltype}"))
                    added.append(col)
                except Exception as e:
                    db.session.rollback()
                    errors.append({'column': col, 'error': str(e)})

            try:
                has = db.session.execute(text("SELECT conname FROM pg_constraint WHERE conname='fk_rutinas_entrenador' LIMIT 1")).fetchone()
                if not has:
                    db.session.execute(text('ALTER TABLE rutinas ADD CONSTRAINT fk_rutinas_entrenador FOREIGN KEY (entrenador_id) REFERENCES entrenadores(id)'))
            except Exception:
                db.session.rollback()

            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': 'commit failed', 'detail': str(e), 'errors': errors}), 500

            return jsonify({'message': 'repair attempted', 'added': added, 'errors': errors}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.exception('admin_repair_rutinas failed')
        return jsonify({'error': 'repair failed', 'detail': str(e)}), 500


# Dev-only helper: promover un usuario a Entrenador
# Solo está habilitado si se define la variable de entorno DEV_PROMOTE_SECRET.
# Uso: POST /api/dev/promote_entrenador  { "email": "user@test.local", "secret": "<secret>" }
# Esto crea una fila Entrenador(usuario_id=usuario.id) si no existe.
@app.route('/api/dev/promote_entrenador', methods=['POST'])
def dev_promote_entrenador():
    secret = os.getenv('DEV_PROMOTE_SECRET')
    # Endpoint disabled si no hay secreto configurado
    if not secret:
        return jsonify({'error': 'not found'}), 404

    data = request.get_json() or {}
    provided = data.get('secret')
    email = data.get('email')
    if not provided or provided != secret:
        return jsonify({'error': 'unauthorized'}), 401

    if not email:
        return jsonify({'error': 'email required'}), 400

    try:
        from database.database import Usuario, Entrenador
        user = Usuario.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404

        # Si ya tiene entrenador, devolvemos 200 con info
        existing = Entrenador.query.filter_by(usuario_id=user.id).first()
        if existing:
            return jsonify({'message': 'already entrenador', 'entrenador_id': existing.id}), 200

        entrenador = Entrenador(usuario_id=user.id)
        db.session.add(entrenador)
        db.session.commit()
        return jsonify({'message': 'entrenador creado', 'entrenador_id': entrenador.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'db error', 'detail': str(e)}), 500


if __name__ == '__main__':
    # Modo debug solo en desarrollo local
    debug = False if DATABASE_URL else True
    # En producción Render asigna el puerto a través de la variable de entorno PORT
    port = int(os.getenv('PORT', '5000'))
    print(f"Starting Flask on 0.0.0.0:{port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)

