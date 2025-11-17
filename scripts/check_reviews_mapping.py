import sqlite3, json, os
repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db = os.path.join(repo, 'database', 'entrenapro.db')
print('DB PATH:', db)
conn = sqlite3.connect(db)
cur = conn.cursor()
try:
    cur.execute("SELECT id, tipo, content_id, estado, creado_por, creado_en FROM content_review ORDER BY creado_en DESC LIMIT 200")
    rows = cur.fetchall()
    out = []
    for r in rows:
        rid, tipo, content_id, estado, creado_por, creado_en = r
        exists = None
        name = None
        try:
            if tipo == 'rutina':
                cur.execute('SELECT id, nombre, entrenador_id FROM rutinas WHERE id = ?', (content_id,))
                rr = cur.fetchone()
                exists = bool(rr)
                name = rr[1] if rr else None
            elif tipo == 'plan':
                cur.execute('SELECT id, nombre, entrenador_id FROM planes_alimenticios WHERE id = ?', (content_id,))
                rr = cur.fetchone()
                exists = bool(rr)
                name = rr[1] if rr else None
        except Exception:
            exists = False
            name = None
        out.append({'review_id': rid, 'tipo': tipo, 'content_id': content_id, 'estado': estado, 'exists': exists, 'content_name': name, 'creado_por': creado_por, 'creado_en': creado_en})
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
except Exception as e:
    print('ERROR', e)
finally:
    conn.close()
