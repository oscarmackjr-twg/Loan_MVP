#specs/discover_backend.py
import os
import re
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')

print(f"Project root: {PROJECT_ROOT}")
print(f"Backend dir:  {BACKEND_DIR}\n")

# --- Show backend directory structure ---
print("=== Backend Directory Structure ===\n")
for root, dirs, files in os.walk(BACKEND_DIR):
    # Skip noise
    dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'node_modules', '.venv', 'venv', 'env')]
    level = root.replace(BACKEND_DIR, '').count(os.sep)
    indent = '  ' * level
    print(f"{indent}[DIR] {os.path.basename(root)}/")
    sub_indent = '  ' * (level + 1)
    for file in sorted(files):
        print(f"{sub_indent}{file}")

# --- Detect framework ---
print("\n=== Framework Detection ===\n")

framework_patterns = {
    'FastAPI': [
        r'from\s+fastapi\s+import',
        r'FastAPI\(\)',
        r'@\w+\.(get|post|put|delete|patch)\(',
        r'APIRouter\(\)',
    ],
    'Flask': [
        r'from\s+flask\s+import',
        r'Flask\(__name__\)',
        r'@\w+\.route\(',
        r'Blueprint\(',
    ],
    'Django': [
        r'from\s+django',
        r'urlpatterns\s*=',
        r'path\(',
        r'from\s+rest_framework',
    ],
    'Express (Node)': [
        r'require\([\'"]express[\'"]\)',
        r'express\.Router\(\)',
        r'app\.(get|post|put|delete)\(',
    ],
}

all_files = []
for root, dirs, files in os.walk(BACKEND_DIR):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', 'node_modules', '.venv', 'venv', 'env')]
    for f in files:
        if f.endswith(('.py', '.js', '.ts')):
            all_files.append(os.path.join(root, f))

framework_hits = {}
route_files = []

for filepath in all_files:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read()
    except Exception:
        continue

    for framework, patterns in framework_patterns.items():
        for pattern in patterns:
            if re.search(pattern, content):
                framework_hits.setdefault(framework, set()).add(
                    os.path.relpath(filepath, PROJECT_ROOT)
                )

    # Detect route/endpoint definitions
    route_indicators = [
        (r'@\w+\.(get|post|put|delete|patch)\(\s*[\'"]([^\'"]+)[\'"]', 'decorator_route'),
        (r'@\w+\.route\(\s*[\'"]([^\'"]+)[\'"]', 'flask_route'),
        (r'\.add_api_route\(\s*[\'"]([^\'"]+)[\'"]', 'add_api_route'),
        (r'path\(\s*[\'"]([^\'"]+)[\'"]', 'django_path'),
    ]

    for pattern, route_type in route_indicators:
        matches = re.findall(pattern, content)
        if matches:
            route_files.append({
                'file': os.path.relpath(filepath, PROJECT_ROOT),
                'type': route_type,
                'match_count': len(matches),
            })

# Report findings
if framework_hits:
    for framework, files in sorted(framework_hits.items(), key=lambda x: -len(x[1])):
        print(f"  {framework} (found in {len(files)} file(s)):")
        for f in sorted(files)[:10]:
            print(f"    - {f}")
        if len(files) > 10:
            print(f"    ... and {len(files) - 10} more")
        print()
else:
    print("  No recognized framework detected.\n")

if route_files:
    print("=== Files Containing Route/Endpoint Definitions ===\n")
    for rf in sorted(route_files, key=lambda x: x['file']):
        print(f"  {rf['file']}  ({rf['type']}, {rf['match_count']} endpoint(s))")
else:
    print("=== No route/endpoint definitions found ===")

# --- Check for existing spec files ---
print("\n=== Existing API Specs Found ===\n")
spec_patterns = ['openapi', 'swagger', 'api-spec', 'schema']
for root, dirs, files in os.walk(PROJECT_ROOT):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.venv', '__pycache__', '.git')]
    for f in files:
        if any(p in f.lower() for p in spec_patterns) or f.endswith(('.yaml', '.yml')):
            print(f"  {os.path.relpath(os.path.join(root, f), PROJECT_ROOT)}")

# --- Check for requirements/dependencies ---
print("\n=== Dependency Files ===\n")
dep_files = ['requirements.txt', 'Pipfile', 'pyproject.toml', 'setup.py',
             'package.json', 'package-lock.json', 'yarn.lock']
for root, dirs, files in os.walk(PROJECT_ROOT):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.venv', '__pycache__', '.git')]
    for f in files:
        if f in dep_files:
            rel_path = os.path.relpath(os.path.join(root, f), PROJECT_ROOT)
            print(f"  {rel_path}")

# --- Output summary as JSON for downstream tooling ---
summary = {
    'project_root': PROJECT_ROOT,
    'frameworks_detected': {k: list(v) for k, v in framework_hits.items()},
    'route_files': route_files,
}
summary_path = os.path.join(PROJECT_ROOT, 'specs', 'backend-discovery.json')
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2)
print(f"\nDiscovery summary saved to: {summary_path}")