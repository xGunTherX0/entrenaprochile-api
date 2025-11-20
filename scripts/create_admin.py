#!/usr/bin/env python3
"""
Crear un usuario admin directo en la base de datos usando la DATABASE_URL.

Uso (PowerShell):
  $Env:DATABASE_URL = 'postgresql://user:pass@host:5432/db'
  python scripts/create_admin.py

El script pedirá email y password, generará el hash y hará INSERT sólo si no
existe un usuario con ese email. Imprime el id creado o el id existente.
"""
import os
import sys
from getpass import getpass
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, text


def main():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print('ERROR: setea la variable de entorno DATABASE_URL antes de ejecutar.')
        print("Ejemplo (PowerShell): $Env:DATABASE_URL = 'postgresql://user:pass@host:5432/db'")
        sys.exit(1)

    email = input('Admin email (ej: admin@test.local): ').strip()
    if not email:
        print('email requerido')
        sys.exit(1)
    pwd = getpass('Admin password (será encriptada): ').strip()
    if not pwd:
        print('password requerido')
        sys.exit(1)

    hashed = generate_password_hash(pwd)

    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Check existing
        row = conn.execute(text('SELECT id FROM usuarios WHERE email = :email'), {'email': email}).fetchone()
        if row:
            print(f'Usuario ya existe con id={row[0]}')
            return

        # Insert and return id (Postgres supports RETURNING)
        try:
            res = conn.execute(text('''
                INSERT INTO usuarios (email, nombre, hashed_password, activo, creado_en)
                VALUES (:email, :nombre, :hashed, true, now()) RETURNING id
            '''), {'email': email, 'nombre': email, 'hashed': hashed})
            new_id = res.fetchone()[0]
            conn.commit()
            print(f'Usuario creado id={new_id} (email={email})')
        except Exception as e:
            print('ERROR al insertar usuario:', e)
            sys.exit(1)


if __name__ == '__main__':
    main()
