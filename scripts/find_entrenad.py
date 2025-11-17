from pathlib import Path
b = Path('backend/app.py').read_bytes()
for i in range(len(b)):
    if b[i:i+9] == b'entrenad':
        print('pos', i, repr(b[i-20:i+40]))
