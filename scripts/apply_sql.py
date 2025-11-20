"""
Script minimal to apply an SQL file to the database using SQLAlchemy.
Usage (PowerShell):
  & .venv\Scripts\Activate.ps1
  $env:DATABASE_URL = 'postgresql://user:pass@host:port/db'
  python .\scripts\apply_sql.py .\scripts\fix_entrenadores_schema.sql

The script runs each top-level SQL statement separately (split on ';') and continues on non-fatal errors.
It logs successes and failures to stdout and to `scripts/apply_sql.log`.
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def normalize_url(url: str) -> str:
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url


def main():
    if len(sys.argv) < 2:
        print('Usage: python apply_sql.py <sql_file>')
        sys.exit(2)
    sql_file = sys.argv[1]
    if not os.path.isfile(sql_file):
        print('SQL file not found:', sql_file)
        sys.exit(2)

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print('Environment variable DATABASE_URL not set. Set it and retry.')
        sys.exit(2)

    database_url = normalize_url(database_url)
    engine = create_engine(database_url, future=True)

    with open(sql_file, 'r', encoding='utf-8') as fh:
        content = fh.read()

    # Remove SQL line comments (--) and split by semicolon into statements.
    # Keep block comments intact. This is a pragmatic splitter for typical migration scripts.
    lines = content.splitlines()
    cleaned_lines = []
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith('--'):
            continue
        cleaned_lines.append(ln)
    cleaned = '\n'.join(cleaned_lines)

    stmts = [s.strip() for s in cleaned.split(';') if s.strip()]

    log_path = os.path.join(os.path.dirname(sql_file), 'apply_sql.log')
    with open(log_path, 'a', encoding='utf-8') as logf:
        logf.write('----\n')
        from datetime import datetime
        logf.write(f'TIME: {datetime.utcnow().isoformat()}\n')
        logf.write(f'FILE: {sql_file}\n')

        for i, stmt in enumerate(stmts, start=1):
            try:
                print(f'Executing statement {i}/{len(stmts)}...')
                logf.write(f'STMT {i}: beginning\n')
                # Run each statement in its own transaction so a single failure doesn't stop the rest
                with engine.begin() as conn:
                    conn.execute(text(stmt))
                print(f'STMT {i} OK')
                logf.write(f'STMT {i}: OK\n')
            except SQLAlchemyError as err:
                # log and continue
                print(f'STMT {i} FAILED: {err}')
                logf.write(f'STMT {i}: FAILED: {repr(err)}\n')
            except Exception as err:
                print(f'STMT {i} FAILED (unknown): {err}')
                logf.write(f'STMT {i}: FAILED (unknown): {repr(err)}\n')

    print('Done. Check', log_path, 'for details.')


if __name__ == '__main__':
    main()
