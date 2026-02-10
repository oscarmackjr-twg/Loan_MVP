# Add your current public IP to the RDS security group so you can connect from your PC
# (e.g. to run init-database.ps1 or use a DB client). Remove the rule when done for security.
# Usage: .\allow-my-ip-rds.ps1 -Region us-east-1 [-Profile name]

param(
    [string]$Region = "us-east-1",
    [string]$Profile = "",
    [string]$AppName = "loan-engine",
    [string]$Environment = "test"
)

$ErrorActionPreference = "Stop"
$sgName = "$AppName-$Environment-rds-sg"
$profileArg = if ($Profile) { "--profile $Profile" } else { "" }

Write-Host "RDS Security Group: allow your IP for PostgreSQL (5432)" -ForegroundColor Cyan

# Get security group ID
$cmd = "aws ec2 describe-security-groups --filters Name=group-name,Values=$sgName --query SecurityGroups[0].GroupId --output text --region $Region"
if ($profileArg) { $cmd = "aws $profileArg ec2 describe-security-groups --filters Name=group-name,Values=$sgName --query SecurityGroups[0].GroupId --output text --region $Region" }
$sgId = Invoke-Expression $cmd
if (-not $sgId -or $sgId -eq "None") {
    Write-Error "Security group not found: $sgName"
    exit 1
}

# Get your public IP
try {
    $myIp = (Invoke-RestMethod -Uri "https://api.ipify.org" -TimeoutSec 5)
} catch {
    Write-Error "Could not detect your public IP. Add it manually in AWS Console: RDS -> VPC security groups -> $sgName -> Edit inbound rules -> Add 44.0.0.0/8 or your IP/32 on port 5432."
    exit 1
}

$cidr = "$myIp/32"
Write-Host "Your IP: $myIp" -ForegroundColor Gray

# Add ingress rule (duplicate rule returns error; that's ok)
# Run via cmd so AWS CLI stderr doesn't cause PowerShell to throw
$addCmd = "aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 5432 --cidr $cidr --region $Region"
if ($profileArg) { $addCmd = "aws $profileArg ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 5432 --cidr $cidr --region $Region" }
$out = cmd /c "$addCmd 2>&1" 2>&1 | Out-String
if ($LASTEXITCODE -eq 0) {
    Write-Host "Added rule: $cidr -> port 5432 on $sgName" -ForegroundColor Green
} else {
    if ("$out" -match "already exists|Duplicate|RuleAlreadyExists") {
        Write-Host "Rule for your IP already exists." -ForegroundColor Yellow
    } else {
        Write-Error "Failed to add rule. Add it in AWS Console: EC2 -> Security Groups -> $sgName -> Inbound rules -> Add $cidr on port 5432."
        exit 1
    }
}

Write-Host ""
Write-Host "You can now run init-database.ps1 from this machine." -ForegroundColor Green
Write-Host "To remove this rule later (recommended): AWS Console -> EC2 -> Security Groups -> $sgName -> Inbound rules -> Delete the rule for $cidr" -ForegroundColor Gray
Write-Host ""
