# This is a Python file for the Flask application.
# It contains various endpoints for user management and routines.
# Ensure to configure the environment variables before running.
import os
from flask import Flask, jsonify, request
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
		return jsonify({'error': 'internal', 'detail': str(e)}), 500

# Configurable CORS: limita orígenes en producción usando la variable de entorno
# `CORS_ORIGINS`. Por defecto permite todos ('*') para facilitar pruebas.
import os as _os
_cors_origins = _os.getenv('CORS_ORIGINS', '*')
# Configure CORS explicitly so preflight (OPTIONS) respuestas incluyan los encabezados necesarios
app.config.setdefault('CORS_HEADERS', 'Content-Type,Authorization')
CORS(app,
	resources={r"/api/*": {"origins": _cors_origins}},
	supports_credentials=True,
	allow_headers=["Content-Type", "Authorization"],
	methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

from werkzeug.security import generate_password_hash, check_password_hash
from backend.auth import generate_token
from sqlalchemy import text


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

	if not check_password_hash(user.hashed_password, password):
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

	# Generar token JWT con user info
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
	entrenador_usuario_id = data.get('entrenador_id') or data.get('user_id')
	nombre = data.get('nombre')
	descripcion = data.get('descripcion')
	nivel = data.get('nivel')
	es_publica = data.get('es_publica', False)

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

	rutina = Rutina(entrenador_id=entrenador.id, nombre=nombre, descripcion=descripcion, nivel=nivel, es_publica=bool(es_publica))
	db.session.add(rutina)
	try:
		db.session.commit()
		return jsonify({'message': 'rutina creada', 'rutina': {'id': rutina.id, 'nombre': rutina.nombre, 'descripcion': rutina.descripcion, 'nivel': rutina.nivel, 'es_publica': rutina.es_publica, 'creado_en': rutina.creado_en.isoformat()}}), 201
	except Exception as e:
		# Fallback resilient handling: rollback, ensure tables, retry once.
		err_str = str(e)
		app.logger.exception('crear_rutina failed: attempting lightweight repair')
		db.session.rollback()
		try:
			with app.app_context():
				# try to ensure tables/columns exist (safe in dev and harmless in prod)
				db.create_all()
				# attempt to ensure cliente_id column exists and is nullable (common schema mismatch)
				try:
					db.session.execute(text('ALTER TABLE rutinas ADD COLUMN IF NOT EXISTS cliente_id INTEGER'))
					# try to drop NOT NULL constraint if present (Postgres)
					try:
						db.session.execute(text('ALTER TABLE rutinas ALTER COLUMN cliente_id DROP NOT NULL'))
					except Exception:
						# ignore if DB doesn't support or constraint not present
						pass
				except Exception:
					# ignore if ALTER or other ops fail; we'll still try the insert
					pass
				# attempt to insert again
				rutina2 = Rutina(entrenador_id=entrenador.id, nombre=nombre, descripcion=descripcion, nivel=nivel, es_publica=bool(es_publica))
				db.session.add(rutina2)
				db.session.commit()
				return jsonify({'message': 'rutina creada after repair', 'rutina': {'id': rutina2.id, 'nombre': rutina2.nombre, 'descripcion': rutina2.descripcion, 'nivel': rutina2.nivel, 'es_publica': rutina2.es_publica, 'creado_en': rutina2.creado_en.isoformat()}}), 201
		except Exception as e2:
			# second failure: return diagnostic information but avoid leaking too many internals in prod
			db.session.rollback()
			app.logger.exception('crear_rutina: repair attempt failed')
			return jsonify({'error': 'db error', 'detail': str(e2)}), 500


@app.route('/api/rutinas/<int:entrenador_usuario_id>', methods=['GET'])
@jwt_required
def listar_rutinas(entrenador_usuario_id):
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
		result.append({'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion, 'nivel': r.nivel, 'es_publica': r.es_publica, 'creado_en': creado_val})
	return jsonify(result), 200


@app.route('/api/rutinas/public', methods=['GET'])
def listar_rutinas_publicas():
	"""Devuelve rutinas públicas (es_publica == True) ordenadas por creación.
	Endpoint público: no requiere JWT. Se intenta ser resiliente ante fallos
	de esquema similar a `listar_rutinas`.
	"""
	try:
		try:
			rutinas = Rutina.query.filter_by(es_publica=True).order_by(Rutina.creado_en.desc()).all()
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
			# intentar obtener nombre del entrenador si existe
			entrenador_nombre = None
			try:
				ent = Entrenador.query.filter_by(id=r.entrenador_id).first()
				if ent and getattr(ent, 'usuario', None):
					entrenador_nombre = ent.usuario.nombre
			except Exception:
				entrenador_nombre = None
			result.append({'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion, 'nivel': r.nivel, 'es_publica': r.es_publica, 'creado_en': creado_val, 'entrenador_nombre': entrenador_nombre, 'entrenador_id': r.entrenador_id, 'entrenador_usuario_id': getattr(ent, 'usuario_id', None) if ent else None})
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
			return jsonify({'error': 'forbidden: rutina not public'}), 403

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

		return jsonify({'id': rutina.id, 'nombre': rutina.nombre, 'descripcion': rutina.descripcion, 'nivel': rutina.nivel, 'es_publica': rutina.es_publica, 'creado_en': creado_val, 'entrenador_nombre': entrenador_nombre, 'entrenador_id': entrenador_id, 'entrenador_usuario_id': entrenador_usuario_id}), 200
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
			return jsonify({'error': 'forbidden: rutina not public'}), 403

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

		return jsonify({'id': rutina.id, 'nombre': rutina.nombre, 'descripcion': rutina.descripcion, 'nivel': rutina.nivel, 'es_publica': rutina.es_publica, 'creado_en': creado_val, 'entrenador_nombre': entrenador_nombre, 'entrenador_id': entrenador_id, 'entrenador_usuario_id': entrenador_usuario_id}), 200
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
			q = text('SELECT r.id, r.nombre, r.descripcion, r.nivel, r.es_publica, r.creado_en FROM rutinas r JOIN cliente_rutina cr ON cr.rutina_id = r.id WHERE cr.cliente_id = :cid ORDER BY r.creado_en DESC')
			rows = db.session.execute(q, {'cid': cliente.id}).fetchall()
			result = []
			for r in rows:
				creado_val = None
				try:
					# r.creado_en may be a datetime or string
					creado_val = r['creado_en'].isoformat() if getattr(r['creado_en'], 'isoformat', None) else str(r['creado_en'])
				except Exception:
					creado_val = None
				result.append({'id': r['id'], 'nombre': r['nombre'], 'descripcion': r['descripcion'], 'nivel': r['nivel'], 'es_publica': r['es_publica'], 'creado_en': creado_val})
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
						result.append({'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion, 'nivel': r.nivel, 'es_publica': r.es_publica, 'creado_en': creado_val})
				# If no rutina_ids or the fallback produced nothing, return empty list instead of 500
				return jsonify(result), 200
			except Exception:
				app.logger.exception('listar_mis_rutinas: ORM fallback also failed')
				# Return an empty list to avoid surfacing a 500 to the frontend for this user-facing call
				return jsonify([]), 200
	except Exception as e:
		app.logger.exception('listar_mis_rutinas failed')
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
			db.session.execute(text('CREATE TABLE IF NOT EXISTS solicitudes_plan (id SERIAL PRIMARY KEY, cliente_id INTEGER NOT NULL, rutina_id INTEGER NOT NULL, estado VARCHAR(50) DEFAULT \'pendiente\', nota TEXT, creado_en TIMESTAMP DEFAULT now())'))
			db.session.commit()
		except Exception:
			db.session.rollback()

		# Insert a new SolicitudPlan
		from database.database import SolicitudPlan
		s = SolicitudPlan(cliente_id=cliente.id, rutina_id=rutina.id, estado='pendiente')
		db.session.add(s)
		db.session.commit()
		return jsonify({'message': 'solicitud creada', 'id': s.id}), 201
	except Exception as e:
		db.session.rollback()
		app.logger.exception('solicitar_plan failed')
		return jsonify({'error': 'db error', 'detail': str(e)}), 500


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
		return jsonify([], 200)

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
			result.append({'id': s.id, 'rutina_id': s.rutina_id, 'rutina_nombre': getattr(rutina, 'nombre', None), 'estado': s.estado, 'nota': s.nota, 'creado_en': creado})
		return jsonify(result), 200
	except Exception as e:
		app.logger.exception('listar_solicitudes_mis failed')
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
	es_publico = bool(data.get('es_publico', False))

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
				if ent:
					entrenador_nombre = getattr(getattr(ent, 'usuario', None), 'nombre', None)
			except Exception:
				entrenador_nombre = None
			result.append({'id': p.id, 'nombre': p.nombre, 'descripcion': p.descripcion, 'contenido': p.contenido, 'es_publico': p.es_publico, 'creado_en': creado, 'entrenador_nombre': entrenador_nombre, 'entrenador_id': p.entrenador_id})
		return jsonify(result), 200
	except Exception as e:
		app.logger.exception('listar_planes_publicos unexpected')
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
		if not plan:
			return jsonify({'error': 'plan not found'}), 404
		from database.database import SolicitudPlan
		s = SolicitudPlan(cliente_id=cliente.id, plan_id=plan.id, estado='pendiente')
		db.session.add(s)
		db.session.commit()
		return jsonify({'message': 'solicitud creada', 'id': s.id}), 201
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

	if nombre is not None:
		rutina.nombre = nombre
	if descripcion is not None:
		rutina.descripcion = descripcion
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
		users = Usuario.query.order_by(Usuario.creado_en.desc()).all()
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
			result.append({'id': u.id, 'email': u.email, 'nombre': u.nombre, 'creado_en': u.creado_en.isoformat(), 'role': urole})
		return jsonify(result), 200
	except Exception as e:
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

	try:
		from database.database import Usuario, Cliente, Entrenador
		user = Usuario.query.filter_by(id=usuario_id).first()
		if not user:
			return jsonify({'error': 'user not found'}), 404

		# borrar relaciones primero para evitar FK
		try:
			Cliente.query.filter_by(usuario_id=user.id).delete()
			Entrenador.query.filter_by(usuario_id=user.id).delete()
			db.session.delete(user)
			db.session.commit()
			return jsonify({'message': 'usuario eliminado'}), 200
		except Exception as e:
			db.session.rollback()
			return jsonify({'error': 'db error', 'detail': str(e)}), 500
	except Exception as e:
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


@app.route('/api/admin/metrics', methods=['GET'])
@jwt_required
def admin_metrics():
	role = request.jwt_payload.get('role')
	if role != 'admin':
		return jsonify({'error': 'forbidden: admin only'}), 403

	# Make metrics resilient: count each table separately and don't return 500
	try:
		from database.database import Usuario, Cliente, Entrenador, Medicion, Rutina
	except Exception as e:
		app.logger.exception('admin_metrics: failed importing models')
		return jsonify({'error': 'db error', 'detail': str(e)}), 500

	errors = []
	# helper to run a count safely
	def _safe_count(obj, name):
		try:
			return obj.query.count()
		except Exception as ex:
			app.logger.exception(f'admin_metrics: count failed for {name}')
			errors.append({'table': name, 'error': str(ex)})
			return None

	total_users = _safe_count(Usuario, 'usuarios')
	total_clientes = _safe_count(Cliente, 'clientes')
	total_entrenadores = _safe_count(Entrenador, 'entrenadores')
	total_mediciones = _safe_count(Medicion, 'mediciones')
	total_rutinas = _safe_count(Rutina, 'rutinas')

	result = {
		'total_users': total_users if total_users is not None else 0,
		'total_clientes': total_clientes if total_clientes is not None else 0,
		'total_entrenadores': total_entrenadores if total_entrenadores is not None else 0,
		'total_mediciones': total_mediciones if total_mediciones is not None else 0,
		'total_rutinas': total_rutinas if total_rutinas is not None else 0,
	}
	if errors:
		# include a concise errors array to help debugging in the frontend logs
		result['errors'] = errors

	return jsonify(result), 200


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

