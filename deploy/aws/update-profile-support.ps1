# Script to add --profile support to all AWS CLI commands in deploy-aws.ps1
# This updates the script to use the Profile parameter consistently

$scriptPath = Join-Path $PSScriptRoot "deploy-aws.ps1"
$content = Get-Content $scriptPath -Raw

# Pattern 1: Replace standalone AWS commands (not in assignments)
# Pattern: aws service command... (with various quote styles)
# We'll use a more targeted approach - replace common patterns

# Replace patterns like: aws ec2 ... (with --region)
$patterns = @(
    # Pattern: aws service --region $Region
    @{
        Find = 'aws ([a-z0-9-]+) (.*?)--region \$Region'
        Replace = 'if (`$Profile) { aws --profile `$Profile $1 $2--region `$Region } else { aws $1 $2--region `$Region }'
    },
    # Pattern: aws service --region $Region --query
    @{
        Find = 'aws ([a-z0-9-]+) (.*?)--region \$Region (.*?)--query'
        Replace = 'if (`$Profile) { aws --profile `$Profile $1 $2--region `$Region $3--query } else { aws $1 $2--region `$Region $3--query }'
    }
)

Write-Host "This approach is complex. Let me create a better solution..."
Write-Host "Instead, I'll update the script to use a helper function pattern."

# Actually, let's use a simpler approach: create a comprehensive update script
# that the user can run, or better yet, let me just update the deploy script
# to use a consistent pattern throughout.
