from pathlib import Path
p = Path('backend/app.py')
b = p.read_bytes()
idx = 0
found = []
for i in range(len(b)-2):
    if b[i] == 92 and b[i+1] == 110 and b[i+2] == 10:  # backslash, 'n', LF
        start = max(0, i-40)
        end = min(len(b), i+40)
        print('OFFSET', i, repr(b[start:end]))
print('done')
