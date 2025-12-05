"""
Script to create the `password_reset_tokens` table in a Postgres database using
DATABASE_URL environment variable.

Usage (PowerShell / bash):
  # set DATABASE_URL (get it from Render dashboard)
  $env:DATABASE_URL = "postgresql://user:pass@host:port/dbname"
  python .\scripts\create_password_reset_table.py

The script:
- connects using SQLAlchemy
- checks whether the table exists
- if missing, creates it (and a simple index)
- prints useful info for manual verification

Important: always take a DB backup or snapshot before running this in production.
"""
import os
import sys
from sqlalchemy import create_engine, text

SQL_CREATE = """
CREATE TABLE IF NOT EXISTS public.password_reset_tokens (
  id SERIAL PRIMARY KEY,
  token VARCHAR(128) NOT NULL UNIQUE,
  usuario_id INTEGER NOT NULL REFERENCES public.usuarios(id),
  expires_at TIMESTAMPTZ NOT NULL,
  used BOOLEAN DEFAULT false
);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_usuario_id ON public.password_reset_tokens(usuario_id);
"""


def main():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('ERROR: DATABASE_URL environment variable is not set.')
        print('Set it to your Postgres connection string and re-run the script.')
        return 2

    print('Connecting to database...')
    try:
        engine = create_engine(db_url)
    except Exception as e:
        print('Failed to create engine:', e)
        return 3

    try:
        with engine.connect() as conn:
            # Check existence using Postgres function
            row = conn.execute(text("SELECT to_regclass('public.password_reset_tokens')")).fetchone()
            exists = bool(row and row[0])
            if exists:
                print('Table already exists: public.password_reset_tokens')
            else:
                print('Table not found. Creating table...')
                conn.execute(text(SQL_CREATE))
                print('Creation statement executed.')

            # Re-check
            row2 = conn.execute(text("SELECT to_regclass('public.password_reset_tokens')")).fetchone()
            if row2 and row2[0]:
                print('Verified: public.password_reset_tokens exists ->', row2[0])
            else:
                print('ERROR: table still does not exist after creation attempt.')
                return 4

            # Optional: show a sample query count (0 rows expected normally)
            try:
                cnt = conn.execute(text('SELECT COUNT(*) FROM public.password_reset_tokens')).fetchone()[0]
                print('Row count in password_reset_tokens:', cnt)
            except Exception as e:
                print('Could not query row count (maybe permission issue):', e)

    except Exception as e:
        print('Database operation failed:', e)
        return 5

    print('Done')
    return 0


if __name__ == '__main__':
    sys.exit(main())
