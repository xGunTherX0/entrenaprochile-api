import os
from sqlalchemy import create_engine, text

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('DATABASE_URL not set')
    raise SystemExit(1)
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

engine = create_engine(db_url)
with engine.connect() as conn:
    try:
        res = conn.execute(text("SELECT to_regclass('public.planes_alimenticios')")).fetchone()
        print('to_regclass:', res)
    except Exception as e:
        print('to_regclass failed:', e)
    try:
        cnt = conn.execute(text('SELECT count(*) FROM planes_alimenticios')).fetchone()
        print('count:', cnt[0])
    except Exception as e:
        print('count failed:', e)
