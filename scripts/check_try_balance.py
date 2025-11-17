p='backend/app.py'
with open(p,'r',encoding='utf-8') as f:
    lines=f.readlines()

stack=[]
for i,l in enumerate(lines, start=1):
    s=l.strip()
    if s.startswith('try:'):
        stack.append(('try',i))
    elif s.startswith('except') or s.startswith('finally'):
        if stack and stack[-1][0]=='try':
            stack.pop()
        else:
            # found except without try
            print('Found except/finally without try at', i, s)

print('Unmatched try blocks (remaining):')
for item in stack[:20]:
    print(item)

# show region around decorator line 457
start=430
end=470
print('\nContext lines %d..%d:\n' % (start,end))
for i in range(start, end+1):
    print(f"{i:4}: {lines[i-1].rstrip()}")
