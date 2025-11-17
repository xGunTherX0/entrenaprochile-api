"""
Normalize indentation in backend/app.py by replacing tabs with 4 spaces.
Creates a backup `backend/app.py.bak.TIMESTAMP` before writing.

Usage (PowerShell):
    python .\scripts\normalize_indentation.py

After running, start the backend:
    python -m backend.app

"""
import io
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'backend', 'app.py')
if not os.path.exists(TARGET):
    print('Target file not found:', TARGET)
    raise SystemExit(1)

with io.open(TARGET, 'r', encoding='utf-8') as fh:
    data = fh.read()

count_tabs = data.count('\t')
if count_tabs == 0:
    print('No tab characters found in', TARGET)
else:
    print(f'Found {count_tabs} tab characters in {TARGET}; creating backup and normalizing...')

# Backup
bak_name = TARGET + '.bak.' + time.strftime('%Y%m%d%H%M%S')
with io.open(bak_name, 'w', encoding='utf-8') as fh:
    fh.write(data)
print('Backup written to', bak_name)

# Simple normalization: replace all tab chars with 4 spaces
normalized = data.replace('\t', '    ')

# Optional: also convert mixed-leading spaces/tabs combos to consistent 4-space indentation
# (We already replaced tabs globally which is usually sufficient.)

with io.open(TARGET, 'w', encoding='utf-8') as fh:
    fh.write(normalized)

print('Normalization complete. Please run:')
print('    python -m backend.app')
print('If you still see an indentation error, paste the traceback here.')
