#!/usr/bin/env python3
"""
Script pequeño para añadir columnas faltantes a la tabla `rutinas`
en la base de datos de desarrollo `database/entrenapro.db`.

Uso (PowerShell):
  & .\.venv\Scripts\Activate.ps1
  python .\scripts\add_missing_rutina_columns.py

El script comprueba las columnas actuales y ejecuta ALTER TABLE
para cada columna faltante. No modifica columnas existentes.
"""
import os
import sys
import sqlite3

HERE = os.path.dirname(__file__)
DB_PATH = os.path.abspath(os.path.join(HERE, '..', 'database', 'entrenapro.db'))

columns = {
    'seccion_descripcion': 'VARCHAR(200)',
    'objetivo_principal': 'TEXT',
    'enfoque_rutina': 'TEXT',
    'cualidades_clave': 'TEXT',
    'duracion_frecuencia': 'TEXT',
    'material_requerido': 'TEXT',
    'instrucciones_estructurales': 'TEXT',
}


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: no se encontró la base de datos en: {DB_PATH}")
        sys.exit(2)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Verificar que existe la tabla rutinas
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rutinas'")
    if not cur.fetchone():
        print("ERROR: la tabla 'rutinas' no existe en la base de datos. Revisa tu esquema.")
        conn.close()
        sys.exit(3)

    cur.execute("PRAGMA table_info(rutinas)")
    existing = [r[1] for r in cur.fetchall()]

    added = []
    for name, typ in columns.items():
        if name in existing:
            print(f"ya existe: {name}")
            continue
        try:
            sql = f"ALTER TABLE rutinas ADD COLUMN {name} {typ};"
            print(f"añadiendo columna: {name} -> {typ}")
            cur.execute(sql)
            added.append(name)
        except sqlite3.OperationalError as e:
            print(f"ERROR añadiendo {name}: {e}")

    conn.commit()
    conn.close()

    if added:
        print("Columnas añadidas:", ", ".join(added))
    else:
        print("No se añadieron columnas (todas ya existen o hubo errores).")


if __name__ == '__main__':
    main()
