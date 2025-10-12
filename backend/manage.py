import sys
import os
from backend import app, db


USAGE = '''Usage: python manage.py [create_tables|drop_tables]
'''


def create_tables():
    # Importa modelos para que SQLAlchemy los conozca
    try:
        from database import database as models  # noqa: F401
    except Exception:
        # Si no encuentra los modelos, seguimos; db.create_all() no hará nada
        pass

    with app.app_context():
        db.create_all()
        print('Tablas creadas correctamente')


def drop_tables():
    # Importa modelos para asegurarse
    try:
        from database import database as models  # noqa: F401
    except Exception:
        pass

    with app.app_context():
        db.drop_all()
        print('Tablas eliminadas correctamente')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'create_tables':
        create_tables()
    elif cmd == 'drop_tables':
        drop_tables()
    else:
        print(USAGE)
        sys.exit(1)
