# Extract the files Codex needs to understand your infrastructure
# Save each to the specs directory for analysis

# ECS Task Definition (this is the most important one)
copy deploy\aws\ecs-task-definition.json specs\ecs-task-definition.json

# Docker configs
copy deploy\Dockerfile specs\Dockerfile
copy deploy\docker-compose.yml specs\docker-compose.yml

# Environment template
copy deploy\aws\env.example specs\env.example

# The main deployment script (we need to parse this)
copy deploy\aws\deploy-aws.ps1 specs\deploy-aws.ps1

# GitHub Actions workflow
copy .github\workflows\deploy-test.yml specs\deploy-test.yml

# EB config (for reference)
copy deploy\aws\eb\Dockerrun.aws.json specs\Dockerrun.aws.json

# Now display the critical ones
Write-Host "=== ECS Task Definition ==="
type specs\ecs-task-definition.json

Write-Host "`n=== Dockerfile ==="
type specs\Dockerfile

Write-Host "`n=== docker-compose.yml ==="
type specs\docker-compose.yml

Write-Host "`n=== env.example ==="
type specs\env.example

Write-Host "`n=== GitHub Actions Workflow ==="
type specs\deploy-test.yml