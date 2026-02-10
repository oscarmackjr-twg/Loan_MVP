# Check if RDS is publicly accessible and security group allows your IP.
# Usage: .\check-rds-access.ps1 -Region us-east-1 [-Profile name]

param(
    [string]$Region = "us-east-1",
    [string]$Profile = "",
    [string]$AppName = "loan-engine",
    [string]$Environment = "test"
)

$ErrorActionPreference = "Stop"
$DBInstanceId = "$AppName-$Environment-db"
$profileArg = if ($Profile) { "--profile $Profile" } else { "" }

Write-Host "Checking RDS instance: $DBInstanceId" -ForegroundColor Cyan

# Get RDS PubliclyAccessible (run via cmd to avoid stderr throwing)
$cmd = "aws rds describe-db-instances --db-instance-identifier $DBInstanceId --query DBInstances[0].PubliclyAccessible --output text --region $Region"
if ($profileArg) { $cmd = "aws $profileArg rds describe-db-instances --db-instance-identifier $DBInstanceId --query DBInstances[0].PubliclyAccessible --output text --region $Region" }
$publicStr = (cmd /c "$cmd 2>&1" 2>&1 | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $publicStr -match "None|error|Error|NotFound") {
    Write-Host "Could not find RDS instance or AWS error. Run with -Profile if using SSO." -ForegroundColor Red
    exit 1
}

$public = ($publicStr -eq "True")
Write-Host "  Publicly accessible: $public" -ForegroundColor $(if ($public) { "Green" } else { "Yellow" })

if (-not $public) {
    Write-Host ""
    Write-Host "RDS is NOT publicly accessible. Your PC cannot connect until you change this." -ForegroundColor Yellow
    Write-Host "Option A - AWS Console:" -ForegroundColor Cyan
    Write-Host "  RDS -> Databases -> $DBInstanceId -> Modify -> set 'Publicly accessible' to Yes -> Apply immediately" -ForegroundColor Gray
    Write-Host "Option B - AWS CLI (after change, wait a few minutes for RDS to apply):" -ForegroundColor Cyan
    $modCmd = "aws rds modify-db-instance --db-instance-identifier $DBInstanceId --publicly-accessible --apply-immediately --region $Region"
    if ($profileArg) { $modCmd = "aws $profileArg rds modify-db-instance --db-instance-identifier $DBInstanceId --publicly-accessible --apply-immediately --region $Region" }
    Write-Host "  $modCmd" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "RDS is publicly accessible. If init-database still times out, ensure your IP is allowed:" -ForegroundColor Green
Write-Host "  .\deploy\aws\allow-my-ip-rds.ps1 -Region $Region$(if($Profile){" -Profile $Profile"})" -ForegroundColor Gray
Write-Host ""
