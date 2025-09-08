#!/usr/bin/env python3
import sys, os, json
try:
    import yaml
except ImportError:
    print('Missing PyYAML. Install with: pip install pyyaml', file=sys.stderr)
    sys.exit(2)

root = os.path.join(os.getcwd(), 'problems')
index = []
for dirpath, _, files in os.walk(root):
    for f in files:
        if not f.endswith('.yaml'):
            continue
        path = os.path.join(dirpath, f)
        try:
            with open(path, 'r') as fh:
                data = yaml.safe_load(fh)
            index.append({
                'id': data.get('id'),
                'title': data.get('title'),
                'category': data.get('category'),
                'difficulty': data.get('difficulty'),
                'path': os.path.relpath(path, os.getcwd())
            })
        except Exception:
            pass

os.makedirs('problems', exist_ok=True)
with open('problems/index.json','w') as out:
    json.dump({'problems': index}, out, indent=2, ensure_ascii=False)
print(f'Generated problems/index.json with {len(index)} entries')
