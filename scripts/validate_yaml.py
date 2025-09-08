#!/usr/bin/env python3
import sys, os, json
try:
    import yaml
except ImportError:
    print('Missing PyYAML. Install with: pip install pyyaml', file=sys.stderr)
    sys.exit(2)

root = os.path.join(os.getcwd(), 'problems')
errors = []
checked = 0
for dirpath, _, files in os.walk(root):
    for f in files:
        if not f.endswith('.yaml'):
            continue
        path = os.path.join(dirpath, f)
        checked += 1
        try:
            with open(path, 'r') as fh:
                data = yaml.safe_load(fh)
            for k in ['id','title','difficulty','category']:
                if k not in data:
                    errors.append({'file': path, 'error': f'missing field: {k}'})
            if 'requirements' not in data or not isinstance(data['requirements'], dict):
                errors.append({'file': path, 'error': 'requirements missing or not a mapping'})
        except Exception as e:
            errors.append({'file': path, 'error': f'parse error: {e}'})

print(json.dumps({'checked': checked, 'errors': errors}, indent=2))
if errors:
    sys.exit(1)
