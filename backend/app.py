import os
from flask import Flask, jsonify, request
from flask_cors import CORS
# Asumiendo que usas Flask-SQLAlchemy para el ORM
from flask_sqlalchemy import SQLAlchemy 

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

	return jsonify({'message': 'ok', 'user_id': user.id}), 200


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

# Inicializa tu ORM
db = SQLAlchemy(app)

# Importa modelos después de inicializar db para evitar importación circular
from database.database import Usuario, Cliente


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

