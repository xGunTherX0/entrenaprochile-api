from pathlib import Path
p=Path('backend/app.py')
b=p.read_bytes()
count=0
for i in range(len(b)):
    if b[i]==10: # LF
        if i==0 or b[i-1]!=13:
            count+=1
            print('LF at', i, 'context', repr(b[max(0,i-30):min(len(b),i+30)]))
print('total bare LF (not CRLF):', count)
