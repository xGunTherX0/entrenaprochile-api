import os
from flask import Flask, jsonify, request
from flask_cors import CORS
# Asumiendo que usas Flask-SQLAlchemy para el ORM

# Inicialización de la aplicación
app = Flask(__name__)

# Configurable CORS: limita orígenes en producción usando la variable de entorno
# `CORS_ORIGINS`. Por defecto permite todos ('*') para facilitar pruebas.
import os as _os
_cors_origins = _os.getenv('CORS_ORIGINS', '*')
CORS(app, resources={r"/api/*": {"origins": _cors_origins}})

from werkzeug.security import generate_password_hash, check_password_hash
from backend.auth import generate_token


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
	SQLALCHEMY_URI = 'sqlite:///../database/entrenapro.db' 
	print("Modo Desarrollo: Conectando a SQLite")

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
	from database.database import Usuario, Cliente, Entrenador  # noqa: F401
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

	try:
		rutina = Rutina(entrenador_id=entrenador.id, nombre=nombre, descripcion=descripcion, nivel=nivel, es_publica=bool(es_publica))
		db.session.add(rutina)
		db.session.commit()
		return jsonify({'message': 'rutina creada', 'rutina': {'id': rutina.id, 'nombre': rutina.nombre, 'descripcion': rutina.descripcion, 'nivel': rutina.nivel, 'es_publica': rutina.es_publica, 'creado_en': rutina.creado_en.isoformat()}}), 201
	except Exception as e:
		db.session.rollback()
		return jsonify({'error': 'db error', 'detail': str(e)}), 500


@app.route('/api/rutinas/<int:entrenador_usuario_id>', methods=['GET'])
@jwt_required
def listar_rutinas(entrenador_usuario_id):
	header_user_id = request.jwt_payload.get('user_id')
	if header_user_id != entrenador_usuario_id:
		return jsonify({'error': 'forbidden: cannot view rutinas of another entrenador'}), 403

	entrenador = Entrenador.query.filter_by(usuario_id=entrenador_usuario_id).first()
	if not entrenador:
		return jsonify({'error': 'entrenador not found'}), 404

	rutinas = Rutina.query.filter_by(entrenador_id=entrenador.id).order_by(Rutina.creado_en.desc()).all()
	result = []
	for r in rutinas:
		result.append({'id': r.id, 'nombre': r.nombre, 'descripcion': r.descripcion, 'nivel': r.nivel, 'es_publica': r.es_publica, 'creado_en': r.creado_en.isoformat()})
	return jsonify(result), 200


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

	try:
		from database.database import Usuario, Cliente, Entrenador, Medicion, Rutina
		total_users = Usuario.query.count()
		total_clientes = Cliente.query.count()
		total_entrenadores = Entrenador.query.count()
		total_mediciones = Medicion.query.count()
		total_rutinas = Rutina.query.count()
		return jsonify({'total_users': total_users, 'total_clientes': total_clientes, 'total_entrenadores': total_entrenadores, 'total_mediciones': total_mediciones, 'total_rutinas': total_rutinas}), 200
	except Exception as e:
		return jsonify({'error': 'db error', 'detail': str(e)}), 500


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

