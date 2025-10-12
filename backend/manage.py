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


def create_user(email: str, password: str, nombre: str = 'Usuario'):
    # importa modelos
    try:
        from database import database as models  # noqa: F401
    except Exception:
        pass

    from werkzeug.security import generate_password_hash
    with app.app_context():
        from database.database import Usuario, Cliente
        existing = Usuario.query.filter_by(email=email).first()
        if existing:
            print('User already exists')
            return
        hashed = generate_password_hash(password)
        user = Usuario(email=email, nombre=nombre, hashed_password=hashed)
        db.session.add(user)
        db.session.commit()
        cliente = Cliente(usuario_id=user.id)
        db.session.add(cliente)
        db.session.commit()
        print('User created with id', user.id)


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
    elif cmd == 'create_user':
        if len(sys.argv) < 4:
            print('Usage: python manage.py create_user EMAIL PASSWORD [NOMBRE]')
            sys.exit(1)
        email = sys.argv[2]
        password = sys.argv[3]
        nombre = sys.argv[4] if len(sys.argv) > 4 else 'Usuario'
        create_user(email, password, nombre)
    elif cmd == 'drop_tables':
        drop_tables()
    else:
        print(USAGE)
        sys.exit(1)
