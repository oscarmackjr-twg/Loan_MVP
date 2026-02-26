# specs/parse_deploy_script.py
import re
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
script_path = os.path.join(PROJECT_ROOT, 'deploy', 'aws', 'deploy-aws.ps1')

with open(script_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Script size: {len(content):,} characters\n")

# --- Extract AWS CLI commands ---
aws_commands = re.findall(r'aws\s+([\w-]+)\s+([\w-]+)([^\n]*)', content)

services = {}
for service, action, args in aws_commands:
    services.setdefault(service, []).append({
        'action': action,
        'args_preview': args.strip()[:120],
    })

print("=== AWS Services Used ===\n")
for service, actions in sorted(services.items()):
    unique_actions = sorted(set(a['action'] for a in actions))
    print(f"  {service}:")
    for action in unique_actions:
        count = sum(1 for a in actions if a['action'] == action)
        print(f"    - {action} (x{count})")

# --- Extract variable assignments (infrastructure config) ---
print("\n=== Infrastructure Variables ===\n")
var_patterns = [
    (r'\$(\w+)\s*=\s*["\']([^"\']+)["\']', 'string'),
    (r'\$(\w+)\s*=\s*(\d+)', 'number'),
]

infra_vars = {}
for pattern, var_type in var_patterns:
    for name, value in re.findall(pattern, content):
        # Filter to likely infrastructure vars
        infra_keywords = ['vpc', 'subnet', 'sg', 'security', 'cluster', 'service',
                         'task', 'ecr', 'repo', 'image', 'port', 'cpu', 'memory',
                         'rds', 'db', 'database', 'bucket', 's3', 'region',
                         'alb', 'target', 'listener', 'cert', 'domain', 'log',
                         'role', 'policy', 'secret', 'app', 'name', 'env']
        if any(kw in name.lower() for kw in infra_keywords):
            infra_vars[name] = {'value': value, 'type': var_type}

for name, info in sorted(infra_vars.items()):
    print(f"  ${name} = {info['value']}")

# --- Extract resource creation patterns ---
print("\n=== Resources Created ===\n")

resource_patterns = {
    'ECS Cluster': r'ecs\s+create-cluster',
    'ECS Service': r'ecs\s+create-service',
    'ECS Task Definition': r'ecs\s+register-task-definition',
    'ECR Repository': r'ecr\s+create-repository',
    'ALB': r'elbv2\s+create-load-balancer',
    'Target Group': r'elbv2\s+create-target-group',
    'Listener': r'elbv2\s+create-listener',
    'Security Group': r'ec2\s+create-security-group',
    'RDS Instance': r'rds\s+create-db-instance',
    'S3 Bucket': r's3(?:api)?\s+create-bucket',
    'Secret': r'secretsmanager\s+create-secret',
    'IAM Role': r'iam\s+create-role',
    'IAM Policy': r'iam\s+(?:create-policy|attach-role-policy|put-role-policy)',
    'CloudWatch Log Group': r'logs\s+create-log-group',
    'VPC': r'ec2\s+create-vpc',
    'Subnet': r'ec2\s+create-subnet',
}

for resource, pattern in resource_patterns.items():
    matches = re.findall(pattern, content, re.IGNORECASE)
    if matches:
        print(f"  ✓ {resource} ({len(matches)} occurrence(s))")

# --- Build structured infra spec ---
infra_spec = {
    'aws_services': {svc: sorted(set(a['action'] for a in acts))
                     for svc, acts in services.items()},
    'infrastructure_variables': {k: v['value'] for k, v in infra_vars.items()},
    'deployment_method': 'ECS via AWS CLI (imperative PowerShell script)',
    'recommendation': 'Convert to Terraform or CDK for Codex generation',
}

out_path = os.path.join(PROJECT_ROOT, 'specs', 'aws-infra-spec.json')
with open(out_path, 'w') as f:
    json.dump(infra_spec, f, indent=2)

print(f"\nInfra spec saved to: {out_path}")