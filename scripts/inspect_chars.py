from pathlib import Path
s = Path('backend/app.py').read_text(encoding='utf-8')
# find the substring @app.route('/api/rutinas/<int:
idx = s.find("@app.route('/api/rutinas/<int:")
print('idx', idx)
if idx==-1:
    print('not found')
else:
    start = max(0, idx-40)
    end = min(len(s), idx+120)
    chunk = s[start:end]
    print('CHUNK repr:')
    print(repr(chunk))
    print('\nCHARS:')
    for i,ch in enumerate(chunk):
        print(start+i, ord(ch), ch if ord(ch)>=32 else repr(ch))
