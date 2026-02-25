# specs/extract_aws_infra.py
import json
import subprocess
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print("=== Project Deployment Artifacts ===\n")

# Check what's in the deploy/ directory
deploy_dir = os.path.join(PROJECT_ROOT, 'deploy')
if os.path.exists(deploy_dir):
    print("[DIR] deploy/")
    for root, dirs, files in os.walk(deploy_dir):
        level = root.replace(deploy_dir, '').count(os.sep)
        indent = '  ' * (level + 1)
        print(f"{indent}[DIR] {os.path.basename(root)}/") if level > 0 else None
        for f in sorted(files):
            filepath = os.path.join(root, f)
            size = os.path.getsize(filepath)
            print(f"{indent}  {f}  ({size:,} bytes)")

# Check for Dockerfiles
print("\n=== Docker Configuration ===\n")
for root, dirs, files in os.walk(PROJECT_ROOT):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.venv', '__pycache__', '.git')]
    for f in files:
        if f in ('Dockerfile', 'docker-compose.yml', 'docker-compose.yaml', '.dockerignore'):
            print(f"  {os.path.relpath(os.path.join(root, f), PROJECT_ROOT)}")

# Check for IaC files
print("\n=== Infrastructure as Code ===\n")
iac_extensions = ('.tf', '.tfvars', '.cfn', '.sam')
iac_files = ('template.yaml', 'template.yml', 'samconfig.toml',
             'cdk.json', 'buildspec.yml', 'appspec.yml', 'taskdef.json',
             'Dockerrun.aws.json', '.ebextensions')
for root, dirs, files in os.walk(PROJECT_ROOT):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '.venv', '__pycache__', '.git')]
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), PROJECT_ROOT)
        if any(f.endswith(ext) for ext in iac_extensions) or f in iac_files:
            print(f"  {rel}")
    for d in dirs:
        if d in ('.ebextensions', '.platform', 'cdk.out'):
            print(f"  [DIR] {os.path.relpath(os.path.join(root, d), PROJECT_ROOT)}/")

# Check for CI/CD
print("\n=== CI/CD Configuration ===\n")
ci_paths = [
    '.github/workflows',
    '.gitlab-ci.yml',
    'buildspec.yml',
    'Jenkinsfile',
    '.circleci',
]
for ci in ci_paths:
    full = os.path.join(PROJECT_ROOT, ci)
    if os.path.exists(full):
        if os.path.isdir(full):
            for f in os.listdir(full):
                print(f"  {ci}/{f}")
        else:
            print(f"  {ci}")

# Check for scripts
print("\n=== Deployment Scripts ===\n")
scripts_dir = os.path.join(PROJECT_ROOT, 'scripts')
if os.path.exists(scripts_dir):
    for f in sorted(os.listdir(scripts_dir)):
        print(f"  scripts/{f}")

# Environment variable inventory
print("\n=== Environment Variables (from backend) ===\n")
env_vars = set()
backend_dir = os.path.join(PROJECT_ROOT, 'backend')
for root, dirs, files in os.walk(backend_dir):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', '.venv')]
    for f in files:
        if f.endswith('.py'):
            try:
                with open(os.path.join(root, f), 'r') as fh:
                    for line in fh:
                        import re
                        matches = re.findall(r'os\.(?:environ|getenv)\s*[\.\[\(]\s*[\'"](\w+)[\'"]', line)
                        env_vars.update(matches)
            except Exception:
                pass

for var in sorted(env_vars):
    print(f"  {var}")

# Dump summary
summary = {
    'deploy_dir_exists': os.path.exists(deploy_dir),
    'env_vars': sorted(env_vars),
}
out_path = os.path.join(PROJECT_ROOT, 'specs', 'aws-infra-discovery.json')
with open(out_path, 'w') as f:
    json.dump(summary, f, indent=2)
print(f"\nSaved to: {out_path}")
