# specs/validate_spec.py
import json
from pathlib import Path

spec_path = Path(__file__).parent / 'openapi-spec.json'

with open(spec_path) as f:
    spec = json.load(f)

print(f"OpenAPI Version: {spec.get('openapi')}")
print(f"Title:           {spec['info']['title']}")
print(f"Description:     {spec['info'].get('description', 'N/A')}")
print(f"API Version:     {spec['info']['version']}")
print(f"Spec Size:       {spec_path.stat().st_size:,} bytes")

paths = spec.get('paths', {})
print(f"\nTotal Paths:     {len(paths)}")

# Endpoint inventory
endpoints = []
for path, methods in paths.items():
    for method, details in methods.items():
        if method in ('get', 'post', 'put', 'delete', 'patch'):
            endpoints.append({
                'method': method.upper(),
                'path': path,
                'summary': details.get('summary', ''),
                'tags': details.get('tags', []),
            })

print(f"Total Endpoints: {len(endpoints)}\n")

# Group by tag
tags = {}
for ep in endpoints:
    tag = ep['tags'][0] if ep['tags'] else 'untagged'
    tags.setdefault(tag, []).append(ep)

print("=" * 65)
print(f"{'METHOD':<8} {'PATH':<40} {'SUMMARY'}")
print("=" * 65)

for tag in sorted(tags.keys()):
    print(f"\n[{tag}]")
    for ep in sorted(tags[tag], key=lambda x: x['path']):
        print(f"  {ep['method']:<6} {ep['path']:<40} {ep['summary'][:40]}")

# Schema inventory
schemas = spec.get('components', {}).get('schemas', {})
print(f"\n{'=' * 65}")
print(f"Pydantic Models / Schemas: {len(schemas)}")
print("=" * 65)
for name in sorted(schemas.keys()):
    props = schemas[name].get('properties', {})
    required = schemas[name].get('required', [])
    print(f"  {name:<35} {len(props)} fields, {len(required)} required")

print(f"\n--- Spec is ready for Codex consumption ---")