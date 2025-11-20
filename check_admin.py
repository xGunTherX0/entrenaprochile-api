#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple check script: prints (id, email, failed_attempts, locked_until) for admin user.

Run: `python check_admin.py` after setting `DATABASE_URL` in your PowerShell session.
"""
import os
import sys
from sqlalchemy import create_engine, text

DB_URL = os.environ.get('DATABASE_URL')
if not DB_URL:
    print('ERROR: DATABASE_URL not set', file=sys.stderr)
    sys.exit(2)

engine = create_engine(DB_URL)

email = 'admin@test.local'  # change if your admin email differs

with engine.connect() as conn:
    row = conn.execute(
        text('SELECT id, email, failed_attempts, locked_until FROM usuarios WHERE email = :email LIMIT 1'),
        {'email': email}
    ).fetchone()

print(row)
