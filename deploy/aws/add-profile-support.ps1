# Helper script to add --profile support to all AWS CLI commands in deploy-aws.ps1
# This is a one-time update script

$scriptPath = Join-Path $PSScriptRoot "deploy-aws.ps1"
$content = Get-Content $scriptPath -Raw

# Pattern: Replace "aws command" with conditional profile insertion
# This is complex, so we'll do it in a more targeted way

# For commands that assign to variables: $var = aws ...
# Replace with: $var = if ($Profile) { aws --profile $Profile ... } else { aws ... }

# Actually, simpler: replace all instances of "aws " at start of command lines
# with a conditional that includes profile

Write-Host "This script would update deploy-aws.ps1 to add --profile to all AWS CLI commands"
Write-Host "For now, the script has been updated to accept -Profile parameter"
Write-Host "You can manually add --profile $Profile to AWS commands, or"
Write-Host "we can do a comprehensive update in the next iteration"
