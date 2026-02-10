# Script to add Invoke-AwsCli wrapper to all AWS CLI commands
# This updates deploy-aws.ps1 to use the profile parameter consistently

$scriptPath = Join-Path $PSScriptRoot "deploy-aws.ps1"
$content = Get-Content $scriptPath -Raw

Write-Host "Updating AWS CLI commands to use Invoke-AwsCli wrapper..."

# Pattern 1: Replace assignments like: $var = aws service command...
# This is complex because we need to preserve the entire command structure
# Let's use a simpler approach: replace common patterns

# Replace: $var = aws service --region $Region
$content = $content -replace '\$([a-zA-Z0-9_]+)\s*=\s*aws\s+([a-z0-9-]+)\s+(.*?)(--region\s+\$Region[^\n]*)', '$$$1 = Invoke-AwsCli $2 $3$4'

# Replace: aws service command (standalone, not assignments)
# This is trickier - we need to be more careful

# Actually, let's do a more targeted replacement
# Replace common AWS service patterns one by one

# EC2 commands
$content = $content -replace 'aws ec2 ', 'Invoke-AwsCli ec2 '
$content = $content -replace 'aws iam ', 'Invoke-AwsCli iam '
$content = $content -replace 'aws logs ', 'Invoke-AwsCli logs '
$content = $content -replace 'aws rds ', 'Invoke-AwsCli rds '
$content = $content -replace 'aws secretsmanager ', 'Invoke-AwsCli secretsmanager '
$content = $content -replace 'aws ecr ', 'Invoke-AwsCli ecr '
$content = $content -replace 'aws ecs ', 'Invoke-AwsCli ecs '
$content = $content -replace 'aws elbv2 ', 'Invoke-AwsCli elbv2 '
$content = $content -replace 'aws sts ', 'Invoke-AwsCli sts '
$content = $content -replace 'aws organizations ', 'Invoke-AwsCli organizations '

# Handle docker commands (they use aws ecr get-login-password)
# These need special handling - they pipe to docker login
# We'll leave those as-is for now since they're already handled

# Write the updated content
$backupPath = $scriptPath + ".backup"
Copy-Item $scriptPath $backupPath
Write-Host "Created backup: $backupPath"

$content | Set-Content $scriptPath -NoNewline
Write-Host "Updated $scriptPath"
Write-Host ""
Write-Host "Note: Some commands may need manual review, especially:"
Write-Host "  - Commands with pipes (|)"
Write-Host "  - Commands with complex quoting"
Write-Host "  - Docker login commands"
Write-Host ""
Write-Host "Test the script before using in production!"
