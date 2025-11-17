from pathlib import Path
b = Path('backend/app.py').read_bytes()
seps = {
    'U+2028': b'\xe2\x80\xa8',
    'U+2029': b'\xe2\x80\xa9',
    'U+0085': b'\xc2\x85'
}
for name, seq in seps.items():
    idx = b.find(seq)
    if idx!=-1:
        print(name, 'found at', idx)
        start = max(0, idx-40)
        end = min(len(b), idx+40)
        print(repr(b[start:end]))
    else:
        print(name, 'not found')
