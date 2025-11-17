#!/usr/bin/env python3
"""
Script seguro para: 1) hacer backup de database/entrenapro.db,
2) eliminar filas duplicadas en content_review (manteniendo la de menor id),
3) crear un índice único en (tipo, content_id).

Uso: python scripts/ensure_content_review_unique.py

Nota: este script asume SQLite. Haz backup manual si lo prefieres.
"""
import sqlite3
import shutil
import os
import time

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'entrenapro.db')

if not os.path.exists(DB_PATH):
    print('ERROR: No se encontró la base de datos en', DB_PATH)
    raise SystemExit(1)

# Backup
stamp = time.strftime('%Y%m%d%H%M%S')
backup_path = DB_PATH + f'.bak.{stamp}'
print('Creando backup de la BD en', backup_path)
shutil.copy2(DB_PATH, backup_path)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

try:
    # Ensure table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='content_review'")
    if not cur.fetchone():
        print('La tabla content_review no existe. Nada que hacer.')
    else:
        # Find duplicates
        print('Buscando duplicados en content_review...')
        cur.execute("SELECT tipo, content_id, COUNT(*) as cnt FROM content_review GROUP BY tipo, content_id HAVING cnt>1")
        dups = cur.fetchall()
        if not dups:
            print('No se encontraron duplicados.')
        else:
            print(f'Encontrados {len(dups)} grupos duplicados. Limpiando...')
            for row in dups:
                tipo = row['tipo']
                content_id = row['content_id']
                # keep the minimum id
                cur.execute("SELECT id FROM content_review WHERE tipo=? AND content_id=? ORDER BY id ASC", (tipo, content_id))
                ids = [r['id'] for r in cur.fetchall()]
                keep = ids[0]
                to_delete = ids[1:]
                if to_delete:
                    cur.execute('BEGIN')
                    cur.execute('DELETE FROM content_review WHERE id IN ({})'.format(','.join('?' for _ in to_delete)), to_delete)
                    cur.execute('COMMIT')
                    print(f'Para (tipo={tipo}, content_id={content_id}) eliminadas ids: {to_delete} (conservada id {keep})')
            print('Duplicados eliminados.')

        # Create unique index
        try:
            print('Creando índice único ux_contentreview_tipo_contentid...')
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_contentreview_tipo_contentid ON content_review(tipo, content_id)")
            conn.commit()
            print('Índice único creado (o ya existía).')
        except Exception as e:
            print('ERROR al crear índice único:', e)
            conn.rollback()

finally:
    conn.close()

print('Script finalizado. Backup en:', backup_path)
