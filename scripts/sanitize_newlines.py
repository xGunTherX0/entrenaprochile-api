from pathlib import Path
p = Path('backend/app.py')
bak = Path('backend/app.py.broken_backup')
if not p.exists():
    print('file missing')
    raise SystemExit(1)
if not bak.exists():
    bak.write_bytes(p.read_bytes())
    print('backup written to', str(bak))
else:
    print('backup already exists', str(bak))
b = p.read_bytes()
# Preserve CRLF pairs; remove any LF (\n) bytes that are NOT part of CRLF (\r\n)
# Strategy: replace CRLF with placeholder, remove remaining LF, restore CRLF
placeholder = b'__CRLF_PLACEHOLDER__'
b2 = b.replace(b'\r\n', placeholder)
# Remove any remaining bare LF
b2 = b2.replace(b'\n', b'')
# Restore CRLF
b2 = b2.replace(placeholder, b'\r\n')
# Write back
p.write_bytes(b2)
print('sanitized file written')
