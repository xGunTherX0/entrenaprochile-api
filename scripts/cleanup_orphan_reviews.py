import shutil, sqlite3, os, datetime, json
repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(repo, 'database', 'entrenapro.db')
if not os.path.exists(db_path):
    print('DB not found:', db_path)
    raise SystemExit(1)

# create backup
bak_name = f'entrenapro.db.bak.{datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")}'
bak_path = os.path.join(repo, 'database', bak_name)
shutil.copy2(db_path, bak_path)
print('Backup created at', bak_path)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
try:
    # Count before
    cur.execute("SELECT COUNT(*) FROM content_review")
    before_total = cur.fetchone()[0]

    # orphan rutina
    cur.execute("SELECT COUNT(*) FROM content_review WHERE tipo='rutina' AND content_id NOT IN (SELECT id FROM rutinas)")
    orphan_r = cur.fetchone()[0]
    # orphan plan
    cur.execute("SELECT COUNT(*) FROM content_review WHERE tipo='plan' AND content_id NOT IN (SELECT id FROM planes_alimenticios)")
    orphan_p = cur.fetchone()[0]

    print('Before cleanup: total=%s, orphan_rutina=%s, orphan_plan=%s' % (before_total, orphan_r, orphan_p))

    # Delete orphans
    cur.execute("DELETE FROM content_review WHERE tipo='rutina' AND content_id NOT IN (SELECT id FROM rutinas)")
    deleted_r = conn.total_changes
    cur.execute("DELETE FROM content_review WHERE tipo='plan' AND content_id NOT IN (SELECT id FROM planes_alimenticios)")
    deleted_p = conn.total_changes - deleted_r

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM content_review")
    after_total = cur.fetchone()[0]

    print('Deleted: rutina=%s, plan=%s' % (deleted_r, deleted_p))
    print('After cleanup: total=%s' % after_total)

    # Show remaining pending reviews
    cur.execute("SELECT id,tipo,content_id,estado,creado_por,creado_en FROM content_review ORDER BY creado_en DESC LIMIT 200")
    rows = cur.fetchall()
    out = [dict(zip(['id','tipo','content_id','estado','creado_por','creado_en'], r)) for r in rows]
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))

except Exception as e:
    print('ERROR during cleanup:', e)
    conn.rollback()
finally:
    conn.close()
