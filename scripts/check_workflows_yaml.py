#!/usr/bin/env python3
# Comprueba sintaxis YAML en .github/workflows
import sys, glob
try:
    import yaml
except Exception:
    print('PyYAML no está instalado', file=sys.stderr)
    sys.exit(2)

files = glob.glob('.github/workflows/*')
if not files:
    print('No workflow files found under .github/workflows')
    sys.exit(0)

failed = 0
for f in files:
    print('---', f)
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            content = fh.read()
        # Try full load
        yaml.safe_load(content)
        print('OK: parsed successfully')
    except Exception as e:
        print('ERROR parsing YAML:', type(e).__name__)
        print(e)
        failed += 1

if failed:
    print(f"Completed with {failed} error(s)")
    sys.exit(1)
else:
    print('All workflow YAML files parsed OK')
    sys.exit(0)
