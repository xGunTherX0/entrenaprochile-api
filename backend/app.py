import os
from flask import Flask, jsonify, request
from flask_cors import CORS
# Asumiendo que usas Flask-SQLAlchemy para el ORM

# Inicialización de la aplicación
app = Flask(__name__)

# Habilita CORS para evitar bloqueos desde el frontend (Netlify). En producción
# deberías restringir el origen a tu dominio (ej: CORS(app, resources={r"/api/*": {"origins": "https://tu-sitio.netlify.app"}})).
CORS(app)

from werkzeug.security import generate_password_hash, check_password_hash


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

	# Devuelve role y nombre para que el frontend pueda redirigir según rol
	return jsonify({'message': 'ok', 'user_id': user.id, 'role': role, 'nombre': user.nombre}), 200


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
			# opcional: puedes crear una fila en Entrenador/Cliente si quieres que sea tratado como tal
			print(f"Admin creado: {ADMIN_EMAIL}")
	except Exception:
		# Si la base de datos aún no está migrada o hay un error, no interrumpimos el arranque
		pass


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


if __name__ == '__main__':
	# Modo debug solo en desarrollo local
	debug = False if DATABASE_URL else True
	app.run(host='0.0.0.0', port=5000, debug=debug)

