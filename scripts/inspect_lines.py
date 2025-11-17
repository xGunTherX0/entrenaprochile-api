from pathlib import Path
p = Path('backend/app.py')
lines = p.read_bytes().splitlines(True)
start = 445
end = 465
for i in range(start, end):
    if i < len(lines):
        b = lines[i]
        print(f"LINE {i+1}: {repr(b)}")
    else:
        print(f"LINE {i+1}: <missing>")
