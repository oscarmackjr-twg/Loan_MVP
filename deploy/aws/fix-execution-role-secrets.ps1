# Fix ECS Task Execution Role so it can pull secrets (GetSecretValue).
# Run this if tasks fail with: "AccessDeniedException: User: arn:aws:sts::...:assumed-role/ecsTaskExecutionRole-loan-engine/... is not authorized to perform: secretsmanager:GetSecretValue"
# Usage: .\fix-execution-role-secrets.ps1 -Region us-east-1 [-Profile name]

param(
    [string]$Region = "us-east-1",
    [string]$Profile = "",
    [string]$AppName = "loan-engine",
    [string]$Environment = "test"
)

$ErrorActionPreference = "Stop"
$RoleName = "ecsTaskExecutionRole-$AppName"

# Get account ID
$accountCmd = "aws sts get-caller-identity --query Account --output text"
if ($Profile) { $accountCmd = "aws --profile $Profile sts get-caller-identity --query Account --output text" }
$accountId = (cmd /c "$accountCmd 2>&1" 2>&1 | Out-String).Trim()
if (-not $accountId -or $accountId -match "error|Error") {
    Write-Host "Could not get account ID. Run: aws sso login --profile $Profile" -ForegroundColor Red
    exit 1
}

$Resource = "arn:aws:secretsmanager:${Region}:${accountId}:secret:${AppName}/${Environment}/*"
$policyDoc = @"
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["secretsmanager:GetSecretValue","secretsmanager:DescribeSecret"],"Resource":"$Resource"}]}
"@

$policyFile = "$env:TEMP\ecs-exec-secrets-fix.json"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($policyFile, $policyDoc, $utf8NoBom)

Write-Host "Attaching SecretsManagerAccess policy to $RoleName..." -ForegroundColor Cyan
$putCmd = "aws iam put-role-policy --role-name $RoleName --policy-name SecretsManagerAccess --policy-document file://$policyFile"
if ($Profile) { $putCmd = "aws --profile $Profile iam put-role-policy --role-name $RoleName --policy-name SecretsManagerAccess --policy-document file://$policyFile" }
cmd /c "$putCmd 2>&1" 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed. Ensure you have iam:PutRolePolicy permission." -ForegroundColor Red
    exit 1
}
Write-Host "Done. ECS will use the new permission on the next task start. Force a new deployment to restart tasks: aws ecs update-service --cluster $AppName-$Environment --service $AppName-$Environment --force-new-deployment --region $Region $(if($Profile){"--profile $Profile"})" -ForegroundColor Green
