#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unlock script: resets failed_attempts to 0 and locked_until to NULL for the admin email.

Usage:
  - Set `DATABASE_URL` in your environment, or pass `--database-url`.
  - Optionally pass `--email` to target a different admin email.

Examples (PowerShell):
  $env:DATABASE_URL = 'postgresql://user:pass@host:port/dbname?sslmode=require'
  python .\\unlock_admin.py

  python .\\unlock_admin.py --database-url 'postgresql://user:pass@host:port/dbname?sslmode=require' --email 'admin@test.local'
"""
import os
import sys
import argparse
from sqlalchemy import create_engine, text


def normalize_db_url(url: str) -> str:
    if not url:
        return url
    # Render sometimes provides postgres://; SQLAlchemy prefers postgresql://
    if url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url


def main():
    p = argparse.ArgumentParser(description='Unlock admin account by resetting failed_attempts and locked_until')
    p.add_argument('--database-url', '-d', help='Database URL (overrides DATABASE_URL env var)')
    p.add_argument('--email', '-e', default=os.environ.get('ADMIN_EMAIL', 'admin@test.local'), help='Admin email to unlock')
    args = p.parse_args()

    db_url = args.database_url or os.environ.get('DATABASE_URL')
    if not db_url:
        print('ERROR: DATABASE_URL not set. Pass --database-url or set DATABASE_URL env var.', file=sys.stderr)
        sys.exit(2)

    db_url = normalize_db_url(db_url)

    try:
        engine = create_engine(db_url)
    except Exception as exc:
        print('ERROR: failed to create engine for DATABASE_URL. Check the URL format.', file=sys.stderr)
        print('DETAILS:', str(exc), file=sys.stderr)
        sys.exit(3)

    email = args.email

    try:
        with engine.begin() as conn:
            res = conn.execute(
                text('UPDATE usuarios SET failed_attempts = 0, locked_until = NULL WHERE email = :email RETURNING id, email, failed_attempts, locked_until'),
                {'email': email}
            )
            row = res.fetchone()
    except Exception as exc:
        print('ERROR: database operation failed', file=sys.stderr)
        print('DETAILS:', str(exc), file=sys.stderr)
        sys.exit(4)

    if row:
        print('Updated:', row)
        return 0
    else:
        print('No row updated for', email)
        return 1


if __name__ == '__main__':
    sys.exit(main())
