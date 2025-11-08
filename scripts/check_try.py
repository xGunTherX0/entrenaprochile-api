import ast
import sys

path = r"c:\Users\carlo\U\EntrenaProChile\backend\app.py"
with open(path, 'r', encoding='utf-8') as f:
    src = f.read()

try:
    tree = ast.parse(src)
except Exception as e:
    print('PARSE ERROR:', e)
    sys.exit(1)

bad = []
for node in ast.walk(tree):
    if isinstance(node, ast.Try):
        # node.handlers is list of except handlers
        # node.finalbody is list of nodes in finally
        if len(node.handlers) == 0 and len(node.finalbody) == 0:
            bad.append(node.lineno)

if bad:
    print('Found try without except/finally at lines:', bad)
    sys.exit(2)
else:
    print('No bare try blocks found')
