from pathlib import Path
s = Path('backend/app.py').read_text(encoding='utf-8')
try:
    compile(s, 'backend/app.py', 'exec')
    print('compiled ok')
except SyntaxError as e:
    print('SyntaxError:', e)
    lineno = e.lineno
    print('lineno', lineno)
    lines = s.splitlines()
    for i in range(max(0, lineno-3), min(len(lines), lineno+3)):
        print(i+1, repr(lines[i]))
except Exception as e:
    print('other error', type(e), e)
