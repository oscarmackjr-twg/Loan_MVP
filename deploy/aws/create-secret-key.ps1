# Create the loan-engine/test/SECRET_KEY secret in Secrets Manager if missing.
# ECS tasks need this for app signing (e.g. JWT/sessions). Run if you see ResourceNotFoundException for SECRET_KEY.
# Usage: .\create-secret-key.ps1 -Region us-east-1 [-Profile name]

param(
    [string]$Region = "us-east-1",
    [string]$Profile = "",
    [string]$AppName = "loan-engine",
    [string]$Environment = "test"
)

$ErrorActionPreference = "Stop"
$SecretName = "$AppName/$Environment/SECRET_KEY"
$profileArg = if ($Profile) { "--profile $Profile" } else { "" }

# Generate 64-char random key (same as deploy-aws.ps1); avoid chars that break shell
$chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
$secretValue = -join ((1..64) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })

Write-Host "Creating secret: $SecretName" -ForegroundColor Cyan
$args = @("secretsmanager", "create-secret", "--name", $SecretName, "--secret-string", $secretValue, "--region", $Region)
if ($Profile) { $args = @("--profile", $Profile) + $args }
$out = & aws @args 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    if ($out -match "ResourceExistsException|already exists") {
        Write-Host "Secret already exists: $SecretName. No change made." -ForegroundColor Yellow
        exit 0
    }
    Write-Host "Failed to create secret:" -ForegroundColor Red
    Write-Host $out -ForegroundColor Gray
    exit 1
}
Write-Host "Created secret: $SecretName" -ForegroundColor Green
Write-Host "Force a new ECS deployment so tasks pull the new secret: aws ecs update-service --cluster $AppName-$Environment --service $AppName-$Environment --force-new-deployment --region $Region $(if($Profile){"--profile $Profile"})" -ForegroundColor Gray
