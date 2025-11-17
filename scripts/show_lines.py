import sys
p = 'backend/app.py'
start = 430
end = 480
with open(p, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, start=1):
        if i >= start and i <= end:
            print(f"{i:4}: {line.rstrip()}")
        if i > end:
            break
print('\nDone')
