import os
from flask import Flask, jsonify
# Asumiendo que usas Flask-SQLAlchemy para el ORM
from flask_sqlalchemy import SQLAlchemy 

# Inicialización de la aplicación
app = Flask(__name__)

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

