#!/usr/bin/env python3
"""
Script de migración ligera para añadir la columna `link_url` a la tabla `rutinas`.

Uso:
  # con venv activado, desde la raíz del repo
  python scripts/add_link_url_column.py

El script intenta detectar la base de datos SQLite usando, en orden:
 - la variable de entorno `DATABASE_URL` si apunta a sqlite (sqlite:///...)
 - `instance/entrenapro.db`
 - `database/entrenapro.db`
 - `database/entrenapro.db.bak` (primer .bak encontrado)

Hace un `ALTER TABLE rutinas ADD COLUMN link_url VARCHAR(512)` y maneja errores
si la columna ya existe.
"""
import os
import sqlite3
import sys
from urllib.parse import urlparse


def find_sqlite_path():
    # 1) DATABASE_URL env var (sqlite:///path)
    dburl = os.getenv('DATABASE_URL')
    if dburl:
        if dburl.startswith('sqlite:///'):
            path = dburl.replace('sqlite:///', '')
            if os.path.isfile(path):
                return path
        # support sqlite://<absolute-path>
        parsed = urlparse(dburl)
        if parsed.scheme == 'sqlite' and parsed.path:
            p = parsed.path
            if os.path.isfile(p):
                return p

    # 2) common candidate paths
    candidates = [
        os.path.join('instance', 'entrenapro.db'),
        os.path.join('database', 'entrenapro.db'),
    ]
    # include any .bak in database/ as fallback
    bak_dir = os.path.join('database')
    if os.path.isdir(bak_dir):
        for fname in os.listdir(bak_dir):
            if fname.lower().endswith('.db') and fname.startswith('entrenapro'):
                candidates.append(os.path.join(bak_dir, fname))

    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def add_column_sqlite(db_path):
    print(f"Usando DB: {db_path}")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    try:
        # Check if column exists: PRAGMA table_info
        cur.execute("PRAGMA table_info(rutinas);")
        cols = [r[1] for r in cur.fetchall()]
        if 'link_url' in cols:
            print('La columna link_url ya existe en la tabla rutinas. Nada que hacer.')
            return 0

        # Add column (SQLite supports ADD COLUMN)
        cur.execute("ALTER TABLE rutinas ADD COLUMN link_url VARCHAR(512);")
        con.commit()
        print('Columna link_url añadida correctamente.')
        return 0
    except sqlite3.OperationalError as e:
        print('Error operacional al intentar añadir la columna:', e)
        return 2
    except Exception as e:
        print('Error inesperado:', e)
        return 3
    finally:
        cur.close()
        con.close()


def main():
    path = find_sqlite_path()
    if not path:
        print('No se encontró un fichero de BD sqlite en las ubicaciones habituales.')
        print('Busque su archivo sqlite (p.ej. instance/entrenapro.db o database/entrenapro.db) y ejecútelo manualmente:')
        print('  sqlite3 <ruta_db> "ALTER TABLE rutinas ADD COLUMN link_url VARCHAR(512);"')
        sys.exit(1)

    code = add_column_sqlite(path)
    sys.exit(code)


if __name__ == '__main__':
    main()
