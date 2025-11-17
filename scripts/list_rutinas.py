import sqlite3, json, os
repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db = os.path.join(repo, 'database', 'entrenapro.db')
print('DB PATH:', db)
conn = sqlite3.connect(db)
cur = conn.cursor()
try:
    cur.execute('SELECT id, entrenador_id, nombre, es_publica, creado_en FROM rutinas ORDER BY creado_en DESC LIMIT 50')
    rows = cur.fetchall()
    out = [dict(zip(['id','entrenador_id','nombre','es_publica','creado_en'], r)) for r in rows]
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
except Exception as e:
    print('ERROR', e)
finally:
    conn.close()
