import io
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'backend' / 'app.py'
src = p.read_bytes()
# try decode utf-8
try:
    s = src.decode('utf-8')
except Exception:
    s = src.decode('latin-1')
count_tabs = s.count('\t')
if count_tabs == 0:
    print('No tab characters found.')
else:
    print(f'Found {count_tabs} tab characters — replacing with 4 spaces...')
    s2 = s.replace('\t', '    ')
    p.write_text(s2, encoding='utf-8')
    print('Rewrite complete.')
    print('New tab count:', p.read_text(encoding='utf-8').count('\t'))
