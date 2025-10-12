import os
import sys
import argparse
from pathlib import Path

# Asegura que el proyecto raíz esté en sys.path para poder importar el paquete `backend`
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def parse_args():
    p = argparse.ArgumentParser(description='Crear tablas en la base de datos usando Flask-SQLAlchemy')
    p.add_argument('--database-url', '-u', help='URL de la base de datos (ej: postgresql://user:pass@host/db)')
    return p.parse_args()


def main():
    args = parse_args()

    # Preferir argumento CLI, luego variable de entorno
    db_url = args.database_url or os.environ.get('DATABASE_URL')
    if not db_url:
        print('ERROR: No se ha proporcionado DATABASE_URL. Usa --database-url o exporta DATABASE_URL en el entorno.')
        sys.exit(1)

    # Establece la variable de entorno para que backend.app la lea
    os.environ['DATABASE_URL'] = db_url

    # Ahora importa la app y la instancia de db
    from backend import app, db  # noqa: E402

    # Importa tus modelos aquí si están en otro módulo para que SQLAlchemy los registre
    # Ejemplo: from database import database as models

    with app.app_context():
        try:
            db.create_all()
            print('\u2705 Tablas creadas con éxito en la base de datos configurada en DATABASE_URL')
        except Exception as e:
            print(f'\u274C Error al crear las tablas: {e}')


if __name__ == '__main__':
    main()
