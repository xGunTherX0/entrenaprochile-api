#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unlock script: resets failed_attempts to 0 and locked_until to NULL for the admin email.

Run: `python unlock_admin.py` after setting `DATABASE_URL` in your PowerShell session.
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

with engine.begin() as conn:
    res = conn.execute(
        text('UPDATE usuarios SET failed_attempts = 0, locked_until = NULL WHERE email = :email RETURNING id, email, failed_attempts, locked_until'),
        {'email': email}
    )
    row = res.fetchone()

if row:
    print('Updated:', row)
else:
    print('No row updated for', email)
