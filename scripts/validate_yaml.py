#!/usr/bin/env python3
import sys, os, json
try:
    import yaml
except ImportError:
    print('Missing PyYAML. Install with: pip install pyyaml', file=sys.stderr)
    sys.exit(2)

try:
    import jsonschema
except Exception:
    jsonschema = None

root = os.path.join(os.getcwd(), 'problems')
parse_errors = []
warnings = []
checked = 0

def should_validate(path: str) -> bool:
    # Validate only known difficulty folders; skip schemas and others
    rel = os.path.relpath(path, root)
    parts = rel.split(os.sep)
    return len(parts) >= 2 and parts[0] in {'basic','intermediate','advanced','expert'}

for dirpath, _, files in os.walk(root):
    for f in files:
        if not f.endswith('.yaml'):
            continue
        path = os.path.join(dirpath, f)
        if not should_validate(path):
            continue
        checked += 1
        try:
            with open(path, 'r') as fh:
                data = yaml.safe_load(fh)
            if not isinstance(data, dict):
                warnings.append({'file': path, 'warning': 'top-level is not a mapping'})
                continue
            # Soft checks (warnings only)
            for k in ['title','difficulty','category']:
                if k not in data:
                    warnings.append({'file': path, 'warning': f'missing field: {k}'})
            if 'requirements' not in data:
                warnings.append({'file': path, 'warning': 'requirements missing'})
            # Schema validation (warning unless jsonschema missing)
            if jsonschema is not None:
                try:
                    schema_path = os.path.join(root, 'schema', 'problem.schema.json')
                    with open(schema_path, 'r') as sf:
                        schema = json.load(sf)
                    jsonschema.validate(instance=data, schema=schema)
                except jsonschema.ValidationError as ve:
                    warnings.append({'file': path, 'warning': f'schema: {ve.message}'})
                except Exception as e:
                    warnings.append({'file': path, 'warning': f'schema-load: {e}'})
        except Exception as e:
            parse_errors.append({'file': path, 'error': f'parse error: {e}'})

print(json.dumps({'checked': checked, 'parse_errors': parse_errors, 'warnings': warnings[:50]}, indent=2))
# Fail build only on parse errors
if parse_errors:
    sys.exit(1)
