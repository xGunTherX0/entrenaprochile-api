"""Add missing columns to the `entrenadores` table in the local SQLite DB.

Run from the repository root with the same Python interpreter used by the app:

    python scripts/add_missing_entrenador_columns.py

This script is idempotent and safe: it checks existing columns before ALTERing.
"""
import os
import sqlite3
import sys


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'entrenapro.db')


def table_has_column(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = [row[1] for row in cur.fetchall()]
    return column in cols


def add_column(conn, table, column_sql):
    try:
        conn.execute(column_sql)
        conn.commit()
        print('OK:', column_sql)
    except Exception as e:
        # SQLite will error if column exists; ignore otherwise report
        print('WARN: could not run:', column_sql, '->', e)


def main():
    if not os.path.exists(DB_PATH):
        print('Database file not found at', DB_PATH)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        # ensure entrenador table exists
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entrenadores'")
        if not cur.fetchone():
            print("Table 'entrenadores' not found in DB; running SQLAlchemy create_all might be needed")
            sys.exit(1)

        # columns to ensure: (column_name, ALTER SQL)
        to_add = [
            ('instagram_url', "ALTER TABLE entrenadores ADD COLUMN instagram_url TEXT"),
            ('youtube_url', "ALTER TABLE entrenadores ADD COLUMN youtube_url TEXT"),
        ]

        for col, sql in to_add:
            if table_has_column(conn, 'entrenadores', col):
                print('Already has column:', col)
            else:
                print('Adding column:', col)
                add_column(conn, 'entrenadores', sql)

        print('Done. Restart the backend (e.g. `python wsgi.py`) and re-test the failing endpoints.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
