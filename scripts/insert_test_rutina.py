"""
Small helper to insert a test `rutina` row directly into the production DB
using SQLAlchemy. This is used only for smoke-testing DB writes when the
HTTP API returns 500 and we need to determine whether the DB itself accepts
INSERTs.

Usage (PowerShell):
  $env:DATABASE_URL='postgresql://USER:PASS@HOST/DB'; python .\scripts\insert_test_rutina.py

This script will look up an `entrenadores` row for `usuario_id=2` (the admin)
and try to insert a minimal rutina row. It prints detailed results and exits
with non-zero code on error.
"""
import os
import sys
from sqlalchemy import create_engine, text

def main():
    dburl = os.environ.get('DATABASE_URL')
    if not dburl:
        print('DATABASE_URL not set', file=sys.stderr)
        sys.exit(2)
    # normalize postgres scheme
    if dburl.startswith('postgres://'):
        dburl = dburl.replace('postgres://', 'postgresql://', 1)
    if dburl.startswith('postgresql://') and 'sslmode=' not in dburl:
        if '?' in dburl:
            dburl = dburl + '&sslmode=require'
        else:
            dburl = dburl + '?sslmode=require'
    print('Connecting to DB...')
    try:
        engine = create_engine(dburl)
        with engine.begin() as conn:
            print('Connected. Looking for entrenador row for usuario_id=2')
            row = conn.execute(text('SELECT id, usuario_id FROM entrenadores WHERE usuario_id = :uid LIMIT 1'), {'uid': 2}).fetchone()
            print('entrenador row:', row)
            if not row:
                print('No entrenador row found for usuario_id=2', file=sys.stderr)
                sys.exit(3)
            eid = row[0]
            print('Attempting INSERT into rutinas with entrenador_id=', eid)
            ins = text("INSERT INTO rutinas (entrenador_id, nombre, descripcion, creado_en, es_publica) VALUES (:eid, :n, :d, now(), false) RETURNING id")
            res = conn.execute(ins, {'eid': eid, 'n': 'direct-smoke-test', 'd': 'smoke insert'})
            new = res.fetchone()
            print('Inserted rutina id:', new[0] if new else None)
    except Exception as e:
        print('Error performing DB operations:', e, file=sys.stderr)
        sys.exit(4)

if __name__ == '__main__':
    main()
