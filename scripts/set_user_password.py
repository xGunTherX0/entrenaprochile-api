#!/usr/bin/env python3
"""
Actualizar el hashed_password de un usuario existente.

Uso:
  $Env:DATABASE_URL = 'postgresql://user:pass@host:5432/db'
  python scripts/set_user_password.py <email> <new_password>

Ejemplo:
  python scripts/set_user_password.py admin@test.local Pass1234

Nota: esto sobrescribe la contraseña del usuario indicado. Úsalo con
precaución y rota credenciales si fue expuesto.
"""
import os
import sys
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text


def main():
    if len(sys.argv) < 3:
        print('Uso: python scripts/set_user_password.py <email> <new_password>')
        sys.exit(1)

    email = sys.argv[1]
    new_password = sys.argv[2]

    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print('ERROR: setea la variable de entorno DATABASE_URL antes de ejecutar.')
        sys.exit(1)

    hashed = generate_password_hash(new_password)
    engine = create_engine(db_url)
    with engine.connect() as conn:
        row = conn.execute(text('SELECT id FROM usuarios WHERE email = :email'), {'email': email}).fetchone()
        if not row:
            print('Usuario no encontrado:', email)
            sys.exit(1)
        uid = row[0]
        try:
            conn.execute(text('UPDATE usuarios SET hashed_password = :h WHERE id = :id'), {'h': hashed, 'id': uid})
            conn.commit()
            print(f'Contraseña actualizada para usuario id={uid}, email={email}')
        except Exception as e:
            print('ERROR actualizando contraseña:', e)
            sys.exit(1)


if __name__ == '__main__':
    main()
