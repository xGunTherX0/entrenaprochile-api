import os
from sqlalchemy import create_engine, text
from datetime import datetime


def main():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('ERROR: DATABASE_URL environment variable not set')
        return 1

    # normalize URL for SQLAlchemy/psycopg2
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)

    print('Connecting to database...')
    engine = create_engine(db_url)
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

    migration_path = os.path.join(os.path.dirname(__file__), 'migrations', '2025-11-08_add_planes_and_solicitudes.sql')
    if not os.path.exists(migration_path):
        print('ERROR: migration file not found at', migration_path)
        return 2

    with engine.begin() as conn:
        try:
            # list existing public tables
            rows = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ")).fetchall()
            tables = [r[0] for r in rows]
            print('Found tables to backup:', tables)
        except Exception as e:
            print('Failed to list tables:', e)
            return 3

        # backup each table by creating a copy table named <table>_backup_<ts>
        for t in tables:
            backup_name = f"{t}_backup_{ts}"
            try:
                print(f'Backing up {t} -> {backup_name} ...')
                conn.execute(text(f'CREATE TABLE IF NOT EXISTS "{backup_name}" AS TABLE "{t}"'))
                print('  OK')
            except Exception as e:
                print('  SKIP/ERROR backing up', t, e)

        # apply migration SQL
        print('Applying migration SQL...')
        try:
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql = f.read()
            # exec_driver_sql supports multi-statement SQL
            conn.exec_driver_sql(sql)
            print('Migration SQL executed successfully')
        except Exception as e:
            print('Migration failed:', e)
            return 4

        # verification: check existence of target tables
        try:
            res = conn.execute(text("SELECT to_regclass('public.planes_alimenticios'), to_regclass('public.solicitudes_plan')")).fetchone()
            print('Verification - to_regclass results:', res)
        except Exception as e:
            print('Verification query failed:', e)
            return 5

    print('Done')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
