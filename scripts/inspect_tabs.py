from pathlib import Path
p=Path('backend/app.py')
s=p.read_text(encoding='utf-8')
for i,line in enumerate(s.splitlines()[:60], start=1):
    print(i, repr(line[:12]))
    if '\t' in line:
        print('  -> LINE', i, 'HAS TAB')
# overall counts
print('\nTOTAL TABS IN FILE:', s.count('\t'))
