import sqlite3, json, os

repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db = os.path.join(repo, 'database', 'entrenapro.db')
print('DB PATH:', db)
if not os.path.exists(db):
    print('DB not found')
    raise SystemExit(1)

conn = sqlite3.connect(db)
cur = conn.cursor()
try:
    cur.execute("SELECT id, tipo, content_id, estado, creado_por, creado_en FROM content_review ORDER BY creado_en DESC LIMIT 200")
    rows = cur.fetchall()
    out = [dict(zip(['id','tipo','content_id','estado','creado_por','creado_en'], r)) for r in rows]
    print(json.dumps(out, indent=2, default=str, ensure_ascii=False))
except Exception as e:
    print('ERROR', str(e))
finally:
    conn.close()
