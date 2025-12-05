# This is a Python file for the Flask application.
# It contains various endpoints for user management and routines.
# Ensure to configure the environment variables before running.
import os
# Load .env in development so local env vars (like GOOGLE_CLIENT_ID) are available.
# This is best-effort: if python-dotenv isn't installed, we silently continue.
try:
    from dotenv import load_dotenv
    # load .env from repo root if present
    load_dotenv()
except Exception:
    pass
from flask import Flask, jsonify, request
# Attempt to import google auth libraries. If missing, avoid crashing the
# whole app at import time so the service can start and we can return a
# clear diagnostic from the specific endpoint.
try:
    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_auth_requests
    _GOOGLE_AUTH_AVAILABLE = True
except Exception:
    google_id_token = None
    google_auth_requests = None
    _GOOGLE_AUTH_AVAILABLE = False
from datetime import datetime
# Mejor configuración CORS: permitimos los encabezados comunes (Authorization, Content-Type)
# y soportamos credenciales si es necesario. `CORS_ORIGINS` puede venir desde entorno.
from flask_cors import CORS
# Asumiendo que usas Flask-SQLAlchemy para el ORM

# Inicialización de la aplicación
app = Flask(__name__)

# WSGI middleware: ensure OPTIONS preflight for /api/* always gets a proper CORS response
# This runs before Flask routing and helps when a proxy or server configuration causes
# OPTIONS to not reach Flask or to be handled differently.
def _options_preflight_middleware(app_wsgi):
    def middleware(environ, start_response):
        try:
            method = environ.get('REQUEST_METHOD', '')
            path = environ.get('PATH_INFO', '')
            if method == 'OPTIONS' and path.startswith('/api/'):
                # Build simple preflight response
                status = '200 OK'
                headers = [
                    ('Content-Type', 'text/plain'),
                ]
                # Determine allowed origin from configured cors_origins_config if possible
                try:
                    allowed = cors_origins_config
                    # default to wildcard
                    allow_origin = '*'
                    if allowed != '*':
                        if isinstance(allowed, (list, tuple)):
                            # We cannot inspect the Origin header here reliably, so expose first
                            allow_origin = allowed[0] if allowed else '*'
                        else:
                            allow_origin = str(allowed)
                    headers.append(('Access-Control-Allow-Origin', allow_origin))
                except Exception:
                    headers.append(('Access-Control-Allow-Origin', '*'))
                if cors_supports_credentials:
                    headers.append(('Access-Control-Allow-Credentials', 'true'))
                headers.append(('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS'))
                headers.append(('Access-Control-Allow-Headers', app.config.get('CORS_HEADERS', 'Content-Type,Authorization')))
                start_response(status, headers)
                return [b'']
        except Exception:
            # don't fail startup; log if possible
            try:
                import logging
                logging.getLogger('app').exception('options_preflight_middleware error')
            except Exception:
                pass
        return app_wsgi(environ, start_response)
    return middleware

# Wrap the Flask WSGI app with the middleware
app.wsgi_app = _options_preflight_middleware(app.wsgi_app)

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
# Default CORS origins handling:
# - If `CORS_ORIGINS` env var is set, use it.
# - Otherwise, if we're running in production (DATABASE_URL present),
#   default to the known Netlify frontend origin so deployed frontend can talk to the API.
# - Otherwise default to localhost dev origin for Vite.
_default_local = 'http://localhost:5173'
_netlify_origin = 'https://cfmc-entrenaprochile.netlify.app'
if _os.getenv('CORS_ORIGINS') is not None:
    _cors_origins = _os.getenv('CORS_ORIGINS')
else:
    if _os.getenv('DATABASE_URL'):
        _cors_origins = _netlify_origin
    else:
        _cors_origins = _default_local

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
            # Build a proper response for preflight that includes the CORS headers
            from flask import make_response
            resp = make_response(('', 200))
            origin = request.headers.get('Origin')
            app.logger.debug('CORS preflight for %s from Origin=%s', request.path, origin)
            allowed = cors_origins_config
            # Resolve allowed origin header value
            if allowed == '*':
                resp.headers['Access-Control-Allow-Origin'] = '*'
            else:
                try:
                    if isinstance(allowed, (list, tuple)):
                        if origin and origin in allowed:
                            resp.headers['Access-Control-Allow-Origin'] = origin
                        else:
                            resp.headers['Access-Control-Allow-Origin'] = allowed[0] if allowed else ''
                    else:
                        resp.headers['Access-Control-Allow-Origin'] = str(allowed)
                except Exception:
                    resp.headers['Access-Control-Allow-Origin'] = '*'

            if cors_supports_credentials:
                resp.headers['Access-Control-Allow-Credentials'] = 'true'
                app.logger.debug('CORS preflight: Allow-Credentials=true')

            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            resp.headers['Access-Control-Allow-Headers'] = app.config.get('CORS_HEADERS', 'Content-Type,Authorization')
            app.logger.debug('CORS preflight response headers: %s', {k: resp.headers.get(k) for k in ['Access-Control-Allow-Origin','Access-Control-Allow-Credentials','Access-Control-Allow-Methods','Access-Control-Allow-Headers']})
            return resp
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
            app.logger.debug('CORS applied to response for %s: Origin=%s, Allow-Origin=%s', request.path, origin, response.headers.get('Access-Control-Allow-Origin'))

            # Allowed methods and headers
            response.headers.setdefault('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            response.headers.setdefault('Access-Control-Allow-Headers', app.config.get('CORS_HEADERS', 'Content-Type,Authorization'))
    except Exception:
        pass
    return response


# Explicitly handle OPTIONS for any /api/* path as a robust fallback.
# Some proxies or deployment environments may not trigger before_request
# for OPTIONS consistently, so having a dedicated route ensures preflight
# always returns the necessary CORS headers.
@app.route('/api/<path:subpath>', methods=['OPTIONS'])
def _api_options(subpath):
    from flask import make_response
    try:
        resp = make_response(('', 200))
        origin = request.headers.get('Origin')
        allowed = cors_origins_config
        if allowed == '*':
            resp.headers['Access-Control-Allow-Origin'] = '*'
        else:
            try:
                if isinstance(allowed, (list, tuple)):
                    if origin and origin in allowed:
                        resp.headers['Access-Control-Allow-Origin'] = origin
                    else:
                        resp.headers['Access-Control-Allow-Origin'] = allowed[0] if allowed else ''
                else:
                    resp.headers['Access-Control-Allow-Origin'] = str(allowed)
            except Exception:
                resp.headers['Access-Control-Allow-Origin'] = '*'

        if cors_supports_credentials:
            resp.headers['Access-Control-Allow-Credentials'] = 'true'

        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = app.config.get('CORS_HEADERS', 'Content-Type,Authorization')
        app.logger.debug('Explicit OPTIONS handled for /api/%s from Origin=%s', subpath, origin)
        return resp
    except Exception:
        app.logger.exception('Error while handling explicit OPTIONS for /api/%s', subpath)
        return ('', 500)


# Specific OPTIONS handlers for known endpoints that the frontend frequently preflights.
# These are added because some environments may route OPTIONS differently; having
# explicit routes increases the chance of matching the preflight and returning CORS headers.
def _build_preflight_response():
    from flask import make_response
    resp = make_response(('', 200))
    origin = request.headers.get('Origin')
    allowed = cors_origins_config
    if allowed == '*':
        resp.headers['Access-Control-Allow-Origin'] = '*'
    else:
        try:
            if isinstance(allowed, (list, tuple)):
                if origin and origin in allowed:
                    resp.headers['Access-Control-Allow-Origin'] = origin
                else:
                    resp.headers['Access-Control-Allow-Origin'] = allowed[0] if allowed else ''
            else:
                resp.headers['Access-Control-Allow-Origin'] = str(allowed)
        except Exception:
            resp.headers['Access-Control-Allow-Origin'] = '*'
    if cors_supports_credentials:
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = app.config.get('CORS_HEADERS', 'Content-Type,Authorization')
    return resp


def _log_preflight(subpath):
    try:
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        fname = os.path.join(logs_dir, 'preflight.log')
        with open(fname, 'a', encoding='utf-8') as fh:
            fh.write('----\n')
            fh.write(f'TIME: {datetime.utcnow().isoformat()}\n')
            fh.write(f'PATH: /api/{subpath}\n')
            fh.write(f'ORIGIN: {request.headers.get("Origin")}\n')
            fh.write('HEADERS:\n')
            for k, v in request.headers.items():
                fh.write(f'  {k}: {v}\n')
    except Exception:
        app.logger.exception('failed to write preflight log')


@app.route('/api/usuarios/login', methods=['OPTIONS'])
def options_login():
    _log_preflight('usuarios/login')
    app.logger.debug('OPTIONS /api/usuarios/login handled by explicit route')
    return _build_preflight_response()


@app.route('/api/usuarios/google_signin', methods=['OPTIONS'])
def options_google_signin():
    _log_preflight('usuarios/google_signin')
    app.logger.debug('OPTIONS /api/usuarios/google_signin handled by explicit route')
    return _build_preflight_response()

from werkzeug.security import generate_password_hash, check_password_hash
from backend.auth import generate_token, jwt_required
from sqlalchemy import text
import traceback


# Helper functions: read minimal Entrenador rows via raw SQL to avoid selecting
# all columns (some deployments have schema drift where columns like `bio`
# are missing and ORM-selects fail). These return a tiny object with only
# the attributes used by handlers (`id`, `usuario_id`). They intentionally
# avoid instantiating SQLAlchemy model objects which trigger full-column
# SELECTs and mapping.
def _safe_entrenador_by_usuario_id(usuario_id):
    try:
        row = db.session.execute(text("SELECT id, usuario_id FROM entrenadores WHERE usuario_id = :uid LIMIT 1"), {'uid': usuario_id}).fetchone()
        if not row:
            return None
        e = type('E', (), {})()
        try:
            keys = row.keys()
            e.id = row['id'] if 'id' in keys else row[0]
            e.usuario_id = row['usuario_id'] if 'usuario_id' in keys else (row[1] if len(row) > 1 else None)
        except Exception:
            e.id = row[0]
            e.usuario_id = row[1] if len(row) > 1 else None
        return e
    except Exception:
        return None


def _safe_entrenador_by_id(entrenador_id):
    try:
        row = db.session.execute(text("SELECT id, usuario_id FROM entrenadores WHERE id = :eid LIMIT 1"), {'eid': entrenador_id}).fetchone()
        if not row:
            return None
        e = type('E', (), {})()
        try:
            keys = row.keys()
            e.id = row['id'] if 'id' in keys else row[0]
            e.usuario_id = row['usuario_id'] if 'usuario_id' in keys else (row[1] if len(row) > 1 else None)
        except Exception:
            e.id = row[0]
            e.usuario_id = row[1] if len(row) > 1 else None
        return e
    except Exception:
        return None


@app.route('/api/usuarios/register', methods=['POST'])
def register_usuario():
    # Allow explicit disabling of public registration in production via ALLOW_REGISTRATION
    allow_reg = os.getenv('ALLOW_REGISTRATION', '0').lower() in ('1', 'true', 'yes') or (not DATABASE_URL)
    if not allow_reg:
        # If registration disabled, allow only admins to create users via API if they supply a valid admin JWT
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            from backend.auth import decode_token
            token = auth_header.split(' ', 1)[1]
            payload = decode_token(token)
            if payload and payload.get('role') == 'admin':
                # allow admin-initiated registration
                pass
            else:
                return jsonify({'error': 'registration disabled'}), 403
        else:
            return jsonify({'error': 'registration disabled'}), 403

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
    try:
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return jsonify({'error': 'email and password required'}), 400

        user = Usuario.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'invalid credentials'}), 401

        # Account lockout disabled: do not block users based on failed attempts.
        # If password is incorrect, simply return invalid credentials without
        # incrementing failed attempt counters or setting lockout timestamps.
        if not check_password_hash(user.hashed_password, password):
            return jsonify({'error': 'invalid credentials'}), 401

        # Determina rol según relaciones (Cliente / Entrenador)
        ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@test.local')
        if user.email == ADMIN_EMAIL:
            role = 'admin'
        else:
            role = 'usuario'
            try:
                row = db.session.execute(text('SELECT 1 FROM entrenadores WHERE usuario_id = :uid LIMIT 1'), {'uid': user.id}).fetchone()
                if row:
                    role = 'entrenador'
                else:
                    row2 = db.session.execute(text('SELECT 1 FROM clientes WHERE usuario_id = :uid LIMIT 1'), {'uid': user.id}).fetchone()
                    if row2:
                        role = 'cliente'
            except Exception:
                role = getattr(user, '_role_fallback', 'usuario')

        # Reset failed attempts on successful login (no-op if fields don't exist)
        try:
            if hasattr(user, 'failed_attempts'):
                user.failed_attempts = 0
            if hasattr(user, 'locked_until'):
                user.locked_until = None
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Generar token JWT con user info (incluye jti desde backend.auth)
        token = generate_token({'user_id': user.id, 'role': role, 'nombre': user.nombre})
        return jsonify({'message': 'ok', 'user_id': user.id, 'role': role, 'nombre': user.nombre, 'token': token}), 200
    except Exception:
        # Persist traceback to a file so we can inspect the exact error on the deployed server
        try:
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            with open(os.path.join(logs_dir, 'login_error.log'), 'a', encoding='utf-8') as fh:
                fh.write('----\n')
                fh.write(f'TIME: {datetime.utcnow().isoformat()}\n')
                fh.write(f'PATH: {getattr(request, "path", None)}\n')
                fh.write('REQUEST_BODY:\n')
                try:
                    fh.write(repr(request.get_json() if request.is_json else request.data) + '\n')
                except Exception:
                    pass
                fh.write('TRACEBACK:\n')
                import traceback as _tb
                fh.write(_tb.format_exc())
                fh.write('\n')
        except Exception:
            # best-effort: avoid raising from logging
            pass
        app.logger.exception('login_usuario: unexpected exception')
        is_prod = bool(os.getenv('DATABASE_URL'))
        if is_prod:
            return jsonify({'error': 'internal server error'}), 500
        else:
            import traceback as _tb
            return jsonify({'error': 'internal', 'detail': _tb.format_exc()}), 500


@app.route('/api/usuarios/forgot', methods=['POST'])
def forgot_password():
    """Request a password reset. Body: { email }

    For development this returns the token in the response. In production
    you should email the token to the user and not expose it in the API.
    """
    try:
        data = request.get_json() or {}
        email = data.get('email')
        if not email:
            return jsonify({'error': 'email required'}), 400

        from database.database import Usuario, PasswordResetToken, db as _db
        user = Usuario.query.filter_by(email=email).first()
        if not user:
            # don't reveal whether the email exists — return success for UX
            return jsonify({'message': 'if the email exists, a reset token was created'}), 200

        import uuid
        from datetime import datetime, timedelta
        token = str(uuid.uuid4())
        expires = datetime.utcnow() + timedelta(hours=1)

        pr = PasswordResetToken(token=token, usuario_id=user.id, expires_at=expires, used=False)
        _db.session.add(pr)
        _db.session.commit()

        # In production: send email with link like https://your.site/reset?token=...
        # For development convenience we return the token in the response.
        return jsonify({'message': 'reset token created', 'token': token, 'expires_at': expires.isoformat()}), 200
    except Exception as e:
        app.logger.exception('forgot_password failed')
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': 'internal', 'detail': str(e)}), 500


@app.route('/api/usuarios/google_signin', methods=['POST'])
def google_signin():
    """Sign in or register a user using a Google ID token (GSI).

    Expects JSON body: { id_token: '...' }
    Uses google-auth to verify JWT signature, issuer, exp, aud.
    Requires email_verified. Creates Usuario + Cliente si no existen.
    Devuelve un JWT local y rol.
    """
    try:
        data = request.get_json() or {}
        raw_token = data.get('id_token')
        desired_role = (data.get('desired_role') or '').lower()
        preferred_name = data.get('nombre') or None
        # Debug/logging: record minimal context to help diagnose production 500s
        try:
            # Mask GOOGLE_CLIENT_ID for logs (show only prefix/suffix)
            _g = os.getenv('GOOGLE_CLIENT_ID')
            if _g:
                _masked = (_g[:4] + '...' + _g[-4:]) if len(_g) > 8 else '*****'
            else:
                _masked = None
            app.logger.info('google_signin called: path=%s remote=%s client_id_set=%s token_len=%s',
                            getattr(request, 'path', None), request.remote_addr, bool(_g), len(raw_token) if raw_token else 0)
            app.logger.debug('GOOGLE_CLIENT_ID masked=%s', _masked)
        except Exception:
            # best-effort logging
            app.logger.exception('google_signin: logging helper failed')
        if not raw_token:
            return jsonify({'error': 'id_token required'}), 400

        audience = os.getenv('GOOGLE_CLIENT_ID')
        if not audience:
            return jsonify({'error': 'server_misconfigured', 'detail': 'GOOGLE_CLIENT_ID not set'}), 500

        # Ensure google auth libs are available at runtime
        if not _GOOGLE_AUTH_AVAILABLE or google_id_token is None or google_auth_requests is None:
            app.logger.error('google_signin attempted but google-auth library is not available')
            return jsonify({'error': 'server_misconfigured', 'detail': 'google-auth library not installed on server'}), 500

        try:
            idinfo = google_id_token.verify_oauth2_token(raw_token, google_auth_requests.Request(), audience)
        except ValueError as ve:
            return jsonify({'error': 'invalid_google_token', 'detail': str(ve)}), 401

        if not idinfo.get('email_verified'):
            return jsonify({'error': 'email_not_verified'}), 401

        email = idinfo.get('email')
        nombre = preferred_name or idinfo.get('name') or email
        google_sub = idinfo.get('sub')
        if not email:
            return jsonify({'error': 'email_required'}), 400

        # Ensure model classes are available regardless of earlier import timing
        try:
            from database.database import Usuario, Cliente, Entrenador, db as _db
        except Exception:
            # fallback: try importing without Entrenador and log the issue
            app.logger.exception('failed to import Entrenador model in google_signin; attempting fallback import')
            from database.database import Usuario, Cliente, db as _db

        user = Usuario.query.filter_by(email=email).first()
        if not user:
            user = Usuario(email=email, nombre=nombre, hashed_password='', google_sub=google_sub)
            _db.session.add(user)
            _db.session.commit()
        else:
            # opcional: actualizar nombre si el usuario proporciona uno nuevo
            try:
                if preferred_name and user.nombre != preferred_name:
                    user.nombre = preferred_name
                    _db.session.add(user)
                    _db.session.commit()
            except Exception:
                _db.session.rollback()

        # Crear entidad según el rol deseado
        if desired_role == 'entrenador':
            row = db.session.execute(text('SELECT 1 FROM entrenadores WHERE usuario_id = :uid LIMIT 1'), {'uid': user.id}).fetchone()
            if not row:
                try:
                    ent = Entrenador(usuario_id=user.id)
                    _db.session.add(ent)
                    _db.session.commit()
                except Exception:
                    _db.session.rollback()
            row_cliente = db.session.execute(text('SELECT 1 FROM clientes WHERE usuario_id = :uid LIMIT 1'), {'uid': user.id}).fetchone()
            if not row_cliente:
                try:
                    cliente = Cliente(usuario_id=user.id)
                    _db.session.add(cliente)
                    _db.session.commit()
                except Exception:
                    _db.session.rollback()
        else:
            # default cliente si no se especifica o se pide cliente
            row_cliente = db.session.execute(text('SELECT 1 FROM clientes WHERE usuario_id = :uid LIMIT 1'), {'uid': user.id}).fetchone()
            if not row_cliente:
                try:
                    cliente = Cliente(usuario_id=user.id)
                    _db.session.add(cliente)
                    _db.session.commit()
                except Exception:
                    _db.session.rollback()
            # crea entrenador sólo si pidió entrenador
            if desired_role == 'entrenador':
                row = db.session.execute(text('SELECT 1 FROM entrenadores WHERE usuario_id = :uid LIMIT 1'), {'uid': user.id}).fetchone()
                if not row:
                    try:
                        ent = Entrenador(usuario_id=user.id)
                        _db.session.add(ent)
                        _db.session.commit()
                    except Exception:
                        _db.session.rollback()

        ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@test.local')
        role = 'admin' if user.email == ADMIN_EMAIL else 'usuario'
        if role != 'admin':
            try:
                row_ent = db.session.execute(text('SELECT 1 FROM entrenadores WHERE usuario_id = :uid LIMIT 1'), {'uid': user.id}).fetchone()
                row_cli = db.session.execute(text('SELECT 1 FROM clientes WHERE usuario_id = :uid LIMIT 1'), {'uid': user.id}).fetchone()
                if desired_role == 'entrenador' and row_ent:
                    role = 'entrenador'
                elif desired_role == 'cliente' and row_cli:
                    role = 'cliente'
                else:
                    if row_ent:
                        role = 'entrenador'
                    elif row_cli:
                        role = 'cliente'
            except Exception:
                role = getattr(user, '_role_fallback', 'usuario')

        token = generate_token({'user_id': user.id, 'role': role, 'nombre': user.nombre})

        return jsonify({'message': 'ok', 'user_id': user.id, 'role': role, 'nombre': user.nombre, 'token': token}), 200
    except Exception as e:
        app.logger.exception('google_signin failed')
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': 'internal', 'detail': str(e)}), 500


@app.route('/api/usuarios/reset_password', methods=['POST'])
def reset_password():
    """Reset password using token. Body: { token, password }
    """
    try:
        data = request.get_json() or {}
        token = data.get('token')
        password = data.get('password')
        if not token or not password:
            return jsonify({'error': 'token and password required'}), 400

        from database.database import PasswordResetToken, Usuario, db as _db
        from datetime import datetime

        pr = PasswordResetToken.query.filter_by(token=token).first()
        if not pr:
            return jsonify({'error': 'invalid token'}), 400
        if pr.used:
            return jsonify({'error': 'token already used'}), 400
        if pr.expires_at < datetime.utcnow():
            return jsonify({'error': 'token expired'}), 400

        user = Usuario.query.filter_by(id=pr.usuario_id).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404

        # Update password
        from werkzeug.security import generate_password_hash
        user.hashed_password = generate_password_hash(password)
        pr.used = True

        _db.session.add(user)
        _db.session.add(pr)
        _db.session.commit()

        return jsonify({'message': 'password updated'}), 200
    except Exception as e:
        app.logger.exception('reset_password failed')
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': 'internal', 'detail': str(e)}), 500


@app.route('/api/usuarios/change_password', methods=['POST'])
@jwt_required
def change_password():
    """Change password for authenticated user.
    Body: { "old_password": "...", "new_password": "..." }
    Requires JWT; verifies current password before updating.
    """
    try:
        data = request.get_json() or {}
        old = data.get('old_password')
        new = data.get('new_password')
        if not old or not new:
            return jsonify({'error': 'old_password and new_password required'}), 400

        token_user_id = request.jwt_payload.get('user_id')
        if not token_user_id:
            return jsonify({'error': 'authentication required'}), 401

        from database.database import Usuario, db as _db

        user = Usuario.query.filter_by(id=token_user_id).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404

        if not check_password_hash(getattr(user, 'hashed_password', ''), old):
            return jsonify({'error': 'invalid current password'}), 401

        user.hashed_password = generate_password_hash(new)
        _db.session.add(user)
        _db.session.commit()

        return jsonify({'message': 'password changed'}), 200
    except Exception as e:
        app.logger.exception('change_password failed')
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': 'internal', 'detail': str(e)}), 500


@app.route('/api/usuarios/set_password', methods=['POST'])
@jwt_required
def set_password():
    """Quick set password for authenticated user.
    Body: { "new_password": "..." }
    This endpoint is intended for development / low-friction flows where
    email infrastructure is not available. It will only allow a password
    set without the old password when the environment variable
    `ALLOW_SIMPLE_PASSWORD_CHANGE` is set to '1' or 'true'. Otherwise it
    returns 403 and the client should call `/change_password` with the
    current password.
    """
    try:
        # Check feature flag. Allow quick set in development (no DATABASE_URL) by default
        allow_flag = os.getenv('ALLOW_SIMPLE_PASSWORD_CHANGE', '0').lower() in ('1', 'true', 'yes')
        allow = allow_flag or (not DATABASE_URL)
        data = request.get_json() or {}
        new = data.get('new_password')
        if not new:
            return jsonify({'error': 'new_password required'}), 400

        if not allow:
            return jsonify({'error': 'simple password change not allowed', 'hint': 'use change_password with old_password'}), 403

        token_user_id = request.jwt_payload.get('user_id')
        if not token_user_id:
            return jsonify({'error': 'authentication required'}), 401

        from database.database import Usuario, db as _db
        user = Usuario.query.filter_by(id=token_user_id).first()
        if not user:
            return jsonify({'error': 'user not found'}), 404

        user.hashed_password = generate_password_hash(new)
        _db.session.add(user)
        _db.session.commit()
        return jsonify({'message': 'password updated'}), 200
    except Exception as e:
        app.logger.exception('set_password failed')
        try:
            db.session.rollback()
        except Exception:
            pass
        return jsonify({'error': 'internal', 'detail': str(e)}), 500


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
    # Avoid using backslashes inside f-string expressions (causes SyntaxError in some parsers).
    replaced_db_file = db_file.replace('\\', '/')
    SQLALCHEMY_URI = "sqlite:///" + replaced_db_file
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
    entrenador = _safe_entrenador_by_usuario_id(header_user_id)
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
            app.logger.exception('crear_rutina: commit failed, attempting resilient save')
            # Ensure session is clean before any repair attempts
            try:
                db.session.rollback()
            except Exception:
                pass

            err_str = str(e)
            # If the error indicates missing columns, attempt idempotent ALTER TABLEs for rutinas
            if 'UndefinedColumn' in err_str or ('column' in err_str and 'does not exist' in err_str) or 'seccion_descripcion' in err_str:
                app.logger.info('crear_rutina: detected missing rutinas column(s), attempting lightweight repair')
                try:
                    with app.app_context():
                        alter_stmts = [
                            "ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS seccion_descripcion TEXT",
                            "ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS objetivo_principal TEXT",
                            "ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS enfoque_rutina TEXT",
                            "ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS cualidades_clave TEXT",
                            "ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS duracion_frecuencia VARCHAR(255)",
                            "ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS material_requerido TEXT",
                            "ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS instrucciones_estructurales TEXT",
                            "ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS link_url VARCHAR(1024)",
                            "ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS nivel VARCHAR(50)",
                            "ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS es_publica BOOLEAN DEFAULT FALSE",
                            "ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS creado_en TIMESTAMP"
                        ]
                        for s in alter_stmts:
                            try:
                                db.session.execute(text(s))
                            except Exception:
                                app.logger.debug('crear_rutina: non-fatal ALTER failed: %s', s)
                        try:
                            db.session.commit()
                        except Exception:
                            db.session.rollback()
                except Exception:
                    app.logger.exception('crear_rutina: schema repair attempt failed')

                # After repair attempt, try the insert again in a fresh transaction
                try:
                    db.session.add(rutina)
                    db.session.commit()
                except Exception as e2:
                    app.logger.exception('crear_rutina: retry after schema repair failed')
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                    
                    return jsonify({'error': 'db error', 'detail': str(e2)}), 500
            else:
                # Non-schema related commit failure: return 500 after rollback and logging
                try:
                    db.session.rollback()
                except Exception:
                    pass
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

        entrenador = _safe_entrenador_by_usuario_id(entrenador_usuario_id)
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
                            'seccion_descripcion': 'TEXT',
                            'objetivo_principal': 'TEXT',
                            'enfoque_rutina': 'TEXT',
                            'cualidades_clave': 'TEXT',
                            'duracion_frecuencia': 'VARCHAR(255)',
                            'material_requerido': 'TEXT',
                            'instrucciones_estructurales': 'TEXT',
                            'link_url': 'VARCHAR(1024)',
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
                ent = _safe_entrenador_by_id(r.entrenador_id)
                # skip rutinas if entrenador was deleted or its usuario is missing
                if not ent or not getattr(ent, 'usuario_id', None):
                    continue
                # Query Usuario.nombre directly to avoid touching Entrenador relationship
                try:
                    urow = db.session.execute(text('SELECT nombre, activo FROM usuarios WHERE id = :uid'), {'uid': ent.usuario_id}).fetchone()
                    if not urow:
                        continue
                    keys = getattr(urow, 'keys', lambda: [])()
                    activo_val = urow['activo'] if 'activo' in keys else (urow[1] if len(urow) > 1 else None)
                    if activo_val is False:
                        continue
                    entrenador_nombre = urow['nombre'] if 'nombre' in keys else (urow[0] if len(urow) > 0 else None)
                except Exception:
                    entrenador_nombre = None
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
                            entrenador = _safe_entrenador_by_id(getattr(rutina, 'entrenador_id', None))
                            if entrenador and getattr(entrenador, 'usuario_id', None) == token_user_id:
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
            ent = _safe_entrenador_by_id(entrenador_id) if entrenador_id else None
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
                            entrenador = _safe_entrenador_by_id(getattr(rutina, 'entrenador_id', None))
                            if entrenador and getattr(entrenador, 'usuario_id', None) == token_user_id:
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
            ent = _safe_entrenador_by_id(entrenador_id) if entrenador_id else None
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
    except Exception:
        app.logger.exception('listar_mis_rutinas: ORM fallback also failed')
        # Return an empty list to avoid surfacing a 500 to the frontend for this user-facing call
        return jsonify([]), 200


@app.route('/api/solicitudes/mis', methods=['GET'])
@jwt_required
def listar_solicitudes_mis():
    token_user_id = request.jwt_payload.get('user_id')
    if not token_user_id:
        return jsonify({'error': 'authentication required'}), 401

    try:
        cliente = Cliente.query.filter_by(usuario_id=token_user_id).first()
    except Exception:
        cliente = None
    if not cliente:
        return jsonify([]), 200

    try:
        from database.database import SolicitudPlan
        sols = SolicitudPlan.query.filter_by(cliente_id=cliente.id).order_by(SolicitudPlan.creado_en.desc()).all()
        result = []
        for s in sols:
            creado = None
            try:
                creado = s.creado_en.isoformat() if getattr(s, 'creado_en', None) else None
            except Exception:
                creado = None
            rutina = None
            try:
                rutina = Rutina.query.filter_by(id=s.rutina_id).first()
            except Exception:
                rutina = None
            # Provide plan/rutina names defensively so the frontend doesn't show 'null'
            rutina_nombre = None
            plan_nombre = None
            try:
                if rutina and getattr(rutina, 'nombre', None):
                    rutina_nombre = rutina.nombre
            except Exception:
                rutina_nombre = None
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



@app.route('/api/rutinas/<int:rutina_id>/solicitar', methods=['POST'])
@jwt_required
def solicitar_plan(rutina_id):
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
        rutina = Rutina.query.filter_by(id=rutina_id).first()
        if not rutina:
            return jsonify({'error': 'rutina not found'}), 404

        # create solicitudes_plan table if missing
        try:
            db.session.execute(text(
                "CREATE TABLE IF NOT EXISTS solicitudes_plan ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "cliente_id INTEGER NOT NULL, "
                "rutina_id INTEGER, "
                "plan_id INTEGER, "
                "estado VARCHAR(50) DEFAULT 'pendiente', "
                "nota TEXT, "
                "creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()

            # Ensure columns exist on older DBs: add plan_id and rutina_id if missing
            try:
                db.session.execute(text("ALTER TABLE solicitudes_plan ADD COLUMN plan_id INTEGER"))
                db.session.execute(text("ALTER TABLE solicitudes_plan ADD COLUMN rutina_id INTEGER"))
                db.session.commit()
            except Exception:
                db.session.rollback()

        from database.database import SolicitudPlan
        # For rutina-based requests we auto-accept (estado 'aceptado') so the
        # cliente sees the solicitud active immediately (workflow: rutina -> plan)
        s = SolicitudPlan(cliente_id=cliente.id, rutina_id=rutina.id, estado='aceptado')
        db.session.add(s)
        db.session.commit()
        creado = None
        try:
            creado = s.creado_en.isoformat() if getattr(s, 'creado_en', None) else None
        except Exception:
            creado = None
        return jsonify({'message': 'solicitud creada', 'id': s.id, 'creado_en': creado}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.exception('solicitar_plan failed')
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
        entrenador = _safe_entrenador_by_usuario_id(token_user_id)
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
        entrenador = _safe_entrenador_by_usuario_id(token_user_id)
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
        entrenador = _safe_entrenador_by_usuario_id(token_user_id)
    except Exception:
        app.logger.exception('crear_plan: entrenador lookup failed')
        return jsonify({'error': 'db error'}), 500
    if not entrenador:
        return jsonify({'error': 'forbidden: not entrenador'}), 403

    data = request.get_json() or {}
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    contenido = data.get('contenido')
    # Allow trainer to mark a plan as public at creation time when provided in the payload.
    # Default to False (not public) if the client does not include the flag.
    try:
        es_publico = bool(data.get('es_publico', False))
    except Exception:
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
        entrenador = _safe_entrenador_by_usuario_id(token_user_id)
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
                ent = _safe_entrenador_by_id(p.entrenador_id)
                # skip plans if entrenador was deleted or its usuario is missing/inactive
                if not ent or not getattr(ent, 'usuario_id', None):
                    continue
                try:
                    from database.database import Usuario
                    u = Usuario.query.filter_by(id=ent.usuario_id).first()
                    if not u or getattr(u, 'activo', True) is False:
                        continue
                    entrenador_nombre = getattr(u, 'nombre', None)
                except Exception:
                    entrenador_nombre = None
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
                            entrenador = _safe_entrenador_by_id(getattr(plan, 'entrenador_id', None))
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
            ent = _safe_entrenador_by_id(plan.entrenador_id)
            if ent:
                # Query Usuario.nombre directly to avoid touching Entrenador relationship
                from database.database import Usuario
                try:
                    urow = db.session.execute(text('SELECT nombre FROM usuarios WHERE id = :uid'), {'uid': ent.usuario_id}).fetchone()
                    if urow:
                        entrenador_nombre = urow['nombre'] if 'nombre' in getattr(urow, 'keys', lambda: [])() else (urow[0] if len(urow) > 0 else None)
                except Exception:
                    entrenador_nombre = None
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
        entrenador = _safe_entrenador_by_usuario_id(token_user_id)
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
        entrenador = _safe_entrenador_by_usuario_id(token_user_id)
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
        entrenador = _safe_entrenador_by_usuario_id(token_user_id)
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
    entrenador = _safe_entrenador_by_id(rutina.entrenador_id)
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

    entrenador = _safe_entrenador_by_id(rutina.entrenador_id)
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

        # Avoid accessing relationship attributes (u.entrenador / u.cliente)
        # because lazy-loading them can trigger SELECTs that reference
        # columns that may be missing (e.g. entrenadores.bio). Instead,
        # fetch the lists of usuario_id from entrenadores and clientes
        # using raw SQL and use those sets to compute roles safely.
        try:
            ent_rows = db.session.execute(text('SELECT usuario_id FROM entrenadores')).fetchall()
            entrenador_user_ids = set([r[0] for r in ent_rows if r and r[0] is not None])
        except Exception:
            entrenador_user_ids = set()
        try:
            cli_rows = db.session.execute(text('SELECT usuario_id FROM clientes')).fetchall()
            cliente_user_ids = set([r[0] for r in cli_rows if r and r[0] is not None])
        except Exception:
            cliente_user_ids = set()

        for u in users:
            try:
                uid = getattr(u, 'id', None)
            except Exception:
                uid = None
            try:
                uemail = getattr(u, 'email', None)
            except Exception:
                uemail = None

            if uemail == ADMIN_EMAIL:
                urole = 'admin'
            elif uid in entrenador_user_ids:
                urole = 'entrenador'
            elif uid in cliente_user_ids:
                urole = 'cliente'
            else:
                # When we created fallback rows they may include _role_fallback
                urole = getattr(u, '_role_fallback', 'usuario')

            # Safe access for created timestamp and activo flag
            try:
                creado_str = u.creado_en.isoformat() if getattr(u, 'creado_en', None) else None
            except Exception:
                creado_str = None
            activo_val = getattr(u, 'activo', True)

            result.append({'id': uid, 'email': uemail, 'nombre': getattr(u, 'nombre', None), 'creado_en': creado_str, 'role': urole, 'activo': activo_val})
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
        from database.database import Rutina, PlanAlimenticio, SolicitudPlan, Cliente, Usuario
        result = []
        # Avoid selecting all columns from entrenadores (some deployments miss columns).
        try:
            rows = db.session.execute(text('SELECT id, usuario_id FROM entrenadores')).fetchall()
        except Exception:
            rows = []
        for rw in rows:
            try:
                keys = getattr(rw, 'keys', lambda: [])()
                ent_id = rw['id'] if 'id' in keys else rw[0]
                usuario_id = rw['usuario_id'] if 'usuario_id' in keys else (rw[1] if len(rw) > 1 else None)
                ent_obj = {'entrenador_id': ent_id, 'usuario_id': usuario_id, 'nombre': None, 'rutinas': [], 'planes': []}
                try:
                    if usuario_id:
                        u = Usuario.query.filter_by(id=usuario_id).first()
                        if u:
                            ent_obj['nombre'] = getattr(u, 'nombre', None)
                except Exception:
                    ent_obj['nombre'] = None
            except Exception:
                continue

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
        existing = _safe_entrenador_by_usuario_id(user.id)
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
                # Run the hard-delete in a single transaction and don't swallow
                # intermediate errors. If anything fails, the whole operation
                # will roll back and a descriptive error will be returned.
                entrenador = _safe_entrenador_by_usuario_id(user.id)

                # Use a robust engine-level transaction to avoid conflicting Session
                # transactions in the app environment (this avoids SQLAlchemy
                # "A transaction is already begun on this Session." errors).
                with db.engine.begin() as conn:
                    # Helper to execute a statement inside a SAVEPOINT so a single
                    # failing DELETE (e.g. due to missing table or FK) does not
                    # abort the whole outer transaction. If the table is missing
                    # we ignore the error; other errors are re-raised.
                    def _exec_savepoint(sql, params=None):
                        try:
                            with conn.begin_nested():
                                if params is None:
                                    conn.execute(text(sql))
                                else:
                                    conn.execute(text(sql), params)
                        except Exception as e:
                            msg = str(e).lower()
                            # Ignore missing relation/table errors (common on prod)
                            if 'does not exist' in msg or 'undefinedtable' in msg or 'relation' in msg and 'does not exist' in msg:
                                return
                            raise
                    # If entrenador exists, remove related content using subqueries so
                    # we don't need to pass Python lists into SQL parameters.
                    if entrenador:
                        ent_id = entrenador.id

                        # Remove solicitudes that reference plans or rutinas owned by this entrenador
                        _exec_savepoint("DELETE FROM solicitudes_plan WHERE plan_id IN (SELECT id FROM planes_alimenticios WHERE entrenador_id = :eid)", {'eid': ent_id})
                        _exec_savepoint("DELETE FROM solicitudes_plan WHERE rutina_id IN (SELECT id FROM rutinas WHERE entrenador_id = :eid)", {'eid': ent_id})

                        # Remove cliente_rutina entries referring to rutinas owned by this entrenador
                        _exec_savepoint("DELETE FROM cliente_rutina WHERE rutina_id IN (SELECT id FROM rutinas WHERE entrenador_id = :eid)", {'eid': ent_id})

                        # Remove content reviews for plans and rutinas owned by this entrenador
                        _exec_savepoint("DELETE FROM content_review WHERE tipo = 'plan' AND content_id IN (SELECT id FROM planes_alimenticios WHERE entrenador_id = :eid)", {'eid': ent_id})
                        _exec_savepoint("DELETE FROM content_review WHERE tipo = 'rutina' AND content_id IN (SELECT id FROM rutinas WHERE entrenador_id = :eid)", {'eid': ent_id})

                        # Delete the actual content rows (plans and rutinas)
                        _exec_savepoint('DELETE FROM planes_alimenticios WHERE entrenador_id = :eid', {'eid': ent_id})
                        _exec_savepoint('DELETE FROM rutinas WHERE entrenador_id = :eid', {'eid': ent_id})

                        # Delete entrenador row
                        _exec_savepoint('DELETE FROM entrenadores WHERE usuario_id = :uid', {'uid': user.id})

                    # Remove any solicitudes or cliente_rutina that reference this user's cliente rows
                    _exec_savepoint("DELETE FROM solicitudes_plan WHERE cliente_id IN (SELECT id FROM clientes WHERE usuario_id = :uid)", {'uid': user.id})
                    _exec_savepoint("DELETE FROM cliente_rutina WHERE cliente_id IN (SELECT id FROM clientes WHERE usuario_id = :uid)", {'uid': user.id})

                    # delete cliente row if exists (raw DELETE to avoid ORM cascade/UPDATE)
                    _exec_savepoint('DELETE FROM clientes WHERE usuario_id = :uid', {'uid': user.id})

                    # Remove any password reset tokens referencing this usuario (FK -> usuarios.id)
                    # In some production DBs this table may not exist (migrations not applied).
                    # Guard against that by swallowing the "relation does not exist" error
                    # so the hard-delete can proceed; re-raise other unexpected errors.
                    try:
                        conn.execute(text('DELETE FROM password_reset_tokens WHERE usuario_id = :uid'), {'uid': user.id})
                    except Exception as e:
                        msg = str(e).lower()
                        if 'does not exist' in msg or 'undefinedtable' in msg or 'password_reset_tokens' in msg:
                            # Table missing — ignore and continue with deletion
                            pass
                        else:
                            raise

                    # finally delete the user row with raw SQL to avoid ORM side-effects
                    _exec_savepoint('DELETE FROM usuarios WHERE id = :uid', {'uid': user.id})

                # Expire the session identity map so further ORM queries see DB changes
                try:
                    db.session.expire_all()
                except Exception:
                    pass

                # If we reach here the transaction committed
                return jsonify({'message': 'usuario eliminado (hard)'}), 200
            except Exception as e:
                # Transaction will be rolled back automatically by session.begin() on exception
                app.logger.exception('admin_delete_usuario hard delete failed')
                return jsonify({'error': 'db error', 'detail': str(e)}), 500

        # Soft delete (default): mark user inactive and unpublish their content so customers don't see it
        try:
            user.activo = False
            # Unpublish entrenador content if present
            entrenador = _safe_entrenador_by_usuario_id(user.id)
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
            existing = _safe_entrenador_by_usuario_id(user.id)
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
            # remove entrenador if exists (raw DELETE to avoid ORM selecting all columns)
            try:
                db.session.execute(text('DELETE FROM entrenadores WHERE usuario_id = :uid'), {'uid': user.id})
                db.session.commit()
            except Exception:
                db.session.rollback()
            return jsonify({'message': 'usuario establecido como cliente (entrenador eliminado si existía)'}), 200

        if desired == 'usuario':
            # remove both relations
            try:
                db.session.execute(text('DELETE FROM entrenadores WHERE usuario_id = :uid'), {'uid': user.id})
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
        entrenador = _safe_entrenador_by_usuario_id(token_user_id)
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
        has_entrenador = True if _safe_entrenador_by_usuario_id(user.id) else False
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
            ent = _safe_entrenador_by_usuario_id(user.id)
            # attempt to read speciality via a minimal raw select (may be NULL/missing)
            speciality = None
            try:
                srow = db.session.execute(text('SELECT speciality FROM entrenadores WHERE usuario_id = :uid'), {'uid': user.id}).fetchone()
                if srow:
                    speciality = srow['speciality'] if 'speciality' in getattr(srow, 'keys', lambda: [])() else (srow[0] if len(srow) > 0 else None)
            except Exception:
                speciality = None
            perfil['entrenador'] = {'id': ent.id, 'speciality': speciality}
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
        from database.database import Usuario
        # Use safe minimal entrenador lookup to avoid selecting missing columns
        ent = _safe_entrenador_by_usuario_id(token_user_id)
        if not ent:
            return jsonify({'error': 'entrenador not found'}), 404
        user = Usuario.query.filter_by(id=token_user_id).first()
        # Try to fetch trainer fields via a minimal raw select; be tolerant of missing columns
        speciality = bio = telefono = instagram_url = youtube_url = None
        try:
            row = db.session.execute(text('SELECT speciality, bio, telefono, instagram_url, youtube_url FROM entrenadores WHERE usuario_id = :uid LIMIT 1'), {'uid': token_user_id}).fetchone()
            if row:
                keys = getattr(row, 'keys', lambda: [])()
                speciality = row['speciality'] if 'speciality' in keys else (row[0] if len(row) > 0 else None)
                bio = row['bio'] if 'bio' in keys else (row[1] if len(row) > 1 else None)
                telefono = row['telefono'] if 'telefono' in keys else (row[2] if len(row) > 2 else None)
                instagram_url = row['instagram_url'] if 'instagram_url' in keys else (row[3] if len(row) > 3 else None)
                youtube_url = row['youtube_url'] if 'youtube_url' in keys else (row[4] if len(row) > 4 else None)
        except Exception:
            # If the wide select fails (schema drift), silently ignore and return minimal profile
            pass

        perfil = {
            'usuario_id': token_user_id,
            'nombre': getattr(user, 'nombre', None),
            'email': getattr(user, 'email', None),
            'speciality': speciality,
            'bio': bio,
            'telefono': telefono,
            'instagram_url': instagram_url,
            'youtube_url': youtube_url,
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
        # Use raw SQL updates so we don't trigger ORM to select all Entrenador columns
        ent = _safe_entrenador_by_usuario_id(token_user_id)
        if not ent:
            return jsonify({'error': 'entrenador not found'}), 404

        # Apply updates per-column in separate statements to tolerate missing columns.
        updated = False
        if 'speciality' in data:
            try:
                db.session.execute(text('UPDATE entrenadores SET speciality = :val WHERE usuario_id = :uid'), {'val': data.get('speciality'), 'uid': token_user_id})
                updated = True
            except Exception:
                db.session.rollback()
        if 'bio' in data:
            try:
                db.session.execute(text('UPDATE entrenadores SET bio = :val WHERE usuario_id = :uid'), {'val': data.get('bio'), 'uid': token_user_id})
                updated = True
            except Exception:
                db.session.rollback()
        if 'telefono' in data:
            try:
                db.session.execute(text('UPDATE entrenadores SET telefono = :val WHERE usuario_id = :uid'), {'val': data.get('telefono'), 'uid': token_user_id})
                updated = True
            except Exception:
                db.session.rollback()
        if 'instagram_url' in data:
            try:
                db.session.execute(text('UPDATE entrenadores SET instagram_url = :val WHERE usuario_id = :uid'), {'val': data.get('instagram_url'), 'uid': token_user_id})
                updated = True
            except Exception:
                db.session.rollback()
        if 'youtube_url' in data:
            try:
                db.session.execute(text('UPDATE entrenadores SET youtube_url = :val WHERE usuario_id = :uid'), {'val': data.get('youtube_url'), 'uid': token_user_id})
                updated = True
            except Exception:
                db.session.rollback()

        if updated:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
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
        from database.database import Usuario
        trainers = []
        # Try a wide select first (may fail if some columns missing like `bio`),
        # fallback to a minimal select of id and usuario_id.
        try:
            rows = db.session.execute(text('SELECT id, usuario_id, speciality, telefono, instagram_url, youtube_url, bio FROM entrenadores ORDER BY id DESC')).fetchall()
        except Exception:
            try:
                rows = db.session.execute(text('SELECT id, usuario_id FROM entrenadores ORDER BY id DESC')).fetchall()
            except Exception:
                rows = []

        ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@test.local')
        for rw in rows:
            try:
                keys = getattr(rw, 'keys', lambda: [])()
                ent_id = rw['id'] if 'id' in keys else rw[0]
                usuario_id = rw['usuario_id'] if 'usuario_id' in keys else (rw[1] if len(rw) > 1 else None)
                # optional fields (may not exist in the minimal fallback)
                speciality = rw['speciality'] if 'speciality' in keys else (rw[2] if len(rw) > 2 else None) if len(rw) > 2 else None
                bio = rw['bio'] if 'bio' in keys else (rw[6] if len(rw) > 6 else None) if len(rw) > 6 else None
                telefono = rw['telefono'] if 'telefono' in keys else (rw[3] if len(rw) > 3 else None) if len(rw) > 3 else None
                instagram_url = rw['instagram_url'] if 'instagram_url' in keys else (rw[4] if len(rw) > 4 else None) if len(rw) > 4 else None
                youtube_url = rw['youtube_url'] if 'youtube_url' in keys else (rw[5] if len(rw) > 5 else None) if len(rw) > 5 else None

                user = Usuario.query.filter_by(id=usuario_id).first()
                if not user or getattr(user, 'activo', True) is False:
                    continue
                # Exclude the configured admin account from trainer lists
                if getattr(user, 'email', None) and getattr(user, 'email') == ADMIN_EMAIL:
                    continue
                trainers.append({'usuario_id': user.id, 'nombre': getattr(user, 'nombre', None), 'speciality': speciality, 'bio': bio, 'telefono': telefono, 'instagram_url': instagram_url, 'youtube_url': youtube_url, 'entrenador_id': ent_id})
            except Exception:
                continue

        return jsonify(trainers), 0 or 200
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
        from database.database import Usuario
        trainers = []
        ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@test.local')
        try:
            rows = db.session.execute(text('SELECT id, usuario_id, speciality, telefono, instagram_url, youtube_url, bio FROM entrenadores ORDER BY id DESC')).fetchall()
        except Exception:
            try:
                rows = db.session.execute(text('SELECT id, usuario_id FROM entrenadores ORDER BY id DESC')).fetchall()
            except Exception:
                rows = []

        for rw in rows:
            try:
                keys = getattr(rw, 'keys', lambda: [])()
                ent_id = rw['id'] if 'id' in keys else rw[0]
                usuario_id = rw['usuario_id'] if 'usuario_id' in keys else (rw[1] if len(rw) > 1 else None)
                speciality = rw['speciality'] if 'speciality' in keys else (rw[2] if len(rw) > 2 else None) if len(rw) > 2 else None
                bio = rw['bio'] if 'bio' in keys else (rw[6] if len(rw) > 6 else None) if len(rw) > 6 else None
                telefono = rw['telefono'] if 'telefono' in keys else (rw[3] if len(rw) > 3 else None) if len(rw) > 3 else None
                instagram_url = rw['instagram_url'] if 'instagram_url' in keys else (rw[4] if len(rw) > 4 else None) if len(rw) > 4 else None
                youtube_url = rw['youtube_url'] if 'youtube_url' in keys else (rw[5] if len(rw) > 5 else None) if len(rw) > 5 else None

                user = Usuario.query.filter_by(id=usuario_id).first()
                if not user or getattr(user, 'activo', True) is False:
                    continue
                # Exclude the configured admin account from public trainer listings
                if getattr(user, 'email', None) and getattr(user, 'email') == ADMIN_EMAIL:
                    continue
                trainers.append({'usuario_id': user.id, 'nombre': getattr(user, 'nombre', None), 'speciality': speciality, 'bio': bio, 'telefono': telefono, 'instagram_url': instagram_url, 'youtube_url': youtube_url})
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
        ent = _safe_entrenador_by_usuario_id(user.id)
        if not ent:
            return jsonify({'error': 'not found'}), 404
        if getattr(user, 'activo', True) is False:
            return jsonify({'error': 'not found'}), 404
        # fetch optional entrenador fields via raw select to avoid missing-column errors
        speciality = bio = instagram_url = youtube_url = telefono = None
        try:
            row = db.session.execute(text('SELECT speciality, bio, instagram_url, youtube_url, telefono FROM entrenadores WHERE usuario_id = :uid LIMIT 1'), {'uid': user.id}).fetchone()
            if row:
                keys = getattr(row, 'keys', lambda: [])()
                speciality = row['speciality'] if 'speciality' in keys else (row[0] if len(row) > 0 else None)
                bio = row['bio'] if 'bio' in keys else (row[1] if len(row) > 1 else None)
                instagram_url = row['instagram_url'] if 'instagram_url' in keys else (row[2] if len(row) > 2 else None)
                youtube_url = row['youtube_url'] if 'youtube_url' in keys else (row[3] if len(row) > 3 else None)
                telefono = row['telefono'] if 'telefono' in keys else (row[4] if len(row) > 4 else None)
        except Exception:
            pass
        perfil = {
            'usuario_id': user.id,
            'nombre': user.nombre,
            'email': getattr(user, 'email', None),
            'speciality': speciality,
            'bio': bio,
            'instagram_url': instagram_url,
            'youtube_url': youtube_url,
            'telefono': telefono,
            'entrenador_id': ent.id,
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
        ent = _safe_entrenador_by_usuario_id(user.id)
        if not ent:
            return jsonify({'error': 'entrenador not found'}), 404
        # if user deactivated, respond 404 to hide profile
        if getattr(user, 'activo', True) is False:
            return jsonify({'error': 'entrenador not found'}), 404

        # fetch optional entrenador fields via raw select to avoid missing-column errors
        speciality = bio = instagram_url = youtube_url = telefono = None
        try:
            row = db.session.execute(text('SELECT speciality, bio, instagram_url, youtube_url, telefono FROM entrenadores WHERE usuario_id = :uid LIMIT 1'), {'uid': user.id}).fetchone()
            if row:
                keys = getattr(row, 'keys', lambda: [])()
                speciality = row['speciality'] if 'speciality' in keys else (row[0] if len(row) > 0 else None)
                bio = row['bio'] if 'bio' in keys else (row[1] if len(row) > 1 else None)
                instagram_url = row['instagram_url'] if 'instagram_url' in keys else (row[2] if len(row) > 2 else None)
                youtube_url = row['youtube_url'] if 'youtube_url' in keys else (row[3] if len(row) > 3 else None)
                telefono = row['telefono'] if 'telefono' in keys else (row[4] if len(row) > 4 else None)
        except Exception:
            pass

        perfil = {
            'usuario_id': user.id,
            'nombre': user.nombre,
            'email': getattr(user, 'email', None),
            'speciality': speciality,
            'bio': bio,
            'instagram_url': instagram_url,
            'youtube_url': youtube_url,
            'telefono': telefono,
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
                entrenador = _safe_entrenador_by_id(getattr(r, 'entrenador_id', None))
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
                entrenador = _safe_entrenador_by_id(getattr(p, 'entrenador_id', None))
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
                entrenador = _safe_entrenador_by_id(getattr(r, 'entrenador_id', None))
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
                entrenador = _safe_entrenador_by_id(getattr(p, 'entrenador_id', None))
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
        existing = _safe_entrenador_by_usuario_id(user.id)
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

