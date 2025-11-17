from pathlib import Path
b = Path('backend/app.py').read_bytes()
needle = b"entrenador_usuario_id"
print('needle in file?', needle in b)
s = b"@app.route('/api/rutinas/<int:"
idx = b.find(s)
print('idx', idx)
if idx!=-1:
    start = max(0, idx-60)
    end = min(len(b), idx+120)
    chunk = b[start:end]
    print('CHUNK BYTES:', chunk)
    for i, byte in enumerate(chunk):
        if byte in (10,13):
            ch = '\\n' if byte==10 else '\\r'
        else:
            try:
                ch = chr(byte)
            except Exception:
                ch = '?'
        print(f"{start+i}: {byte} {ch}")
else:
    print('decorator prefix not found')
