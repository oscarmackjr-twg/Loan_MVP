# Quick diagnostic for 503 Service Unavailable
# Run from repo root or deploy/aws. Usage: .\diagnose-503.ps1 -Region us-east-1 [-Profile name]

param(
    [string]$Region = "us-east-1",
    [string]$Profile = "",
    [string]$ClusterName = "loan-engine-test",
    [string]$ServiceName = "loan-engine-test",
    [string]$TargetGroupName = "loan-engine-test-tg"
)

$profileArg = if ($Profile) { "--profile $Profile" } else { "" }

Write-Host "`n=== 503 Diagnostic: Loan Engine ===`n" -ForegroundColor Cyan

# 1. ECS service
Write-Host "1. ECS Service status" -ForegroundColor Yellow
$cmd = "aws ecs describe-services --cluster $ClusterName --services $ServiceName --region $Region --output json"
if ($profileArg) { $cmd = "aws $profileArg ecs describe-services --cluster $ClusterName --services $ServiceName --region $Region --output json" }
$svcJson = cmd /c "$cmd 2>&1" 2>&1 | Out-String
if (-not $svcJson -or $svcJson -match "error|Error|denied") {
    Write-Host "   Could not run AWS CLI (check credentials/profile).`n" -ForegroundColor Red
} else {
$svc = $svcJson.Trim() | ConvertFrom-Json
if ($svc.services.Count -eq 0) {
    Write-Host "   Service not found (MISSING). Run deploy-aws.ps1 to create it.`n" -ForegroundColor Red
} else {
    $s = $svc.services[0]
    Write-Host "   Running: $($s.runningCount)  Desired: $($s.desiredCount)  Status: $($s.status)" -ForegroundColor $(if ($s.runningCount -eq 0) { "Red" } else { "Green" })
    if ($s.events.Count -gt 0) {
        Write-Host "   Latest event: $($s.events[0].message)"
    }
    Write-Host ""
}
}

# 2. Target health
Write-Host "2. ALB Target health" -ForegroundColor Yellow
$cmd2 = "aws elbv2 describe-target-groups --names $TargetGroupName --region $Region --output json"
if ($profileArg) { $cmd2 = "aws $profileArg elbv2 describe-target-groups --names $TargetGroupName --region $Region --output json" }
$tg = (cmd /c "$cmd2 2>&1" 2>&1 | Out-String).Trim() | ConvertFrom-Json
if (-not $tg -or -not $tg.TargetGroups -or $tg.TargetGroups.Count -eq 0) {
    Write-Host "   Target group not found.`n" -ForegroundColor Red
} else {
    $tgArn = $tg.TargetGroups[0].TargetGroupArn
    $cmd3 = "aws elbv2 describe-target-health --target-group-arn $tgArn --region $Region --output json"
    if ($profileArg) { $cmd3 = "aws $profileArg elbv2 describe-target-health --target-group-arn $tgArn --region $Region --output json" }
    $health = (cmd /c "$cmd3 2>&1" 2>&1 | Out-String).Trim() | ConvertFrom-Json
    $healthy = ($health.TargetHealthDescriptions | Where-Object { $_.TargetHealth.State -eq "healthy" }).Count
    $unhealthy = ($health.TargetHealthDescriptions | Where-Object { $_.TargetHealth.State -eq "unhealthy" }).Count
    $none = ($health.TargetHealthDescriptions | Where-Object { $_.TargetHealth.State -eq "initial" }).Count
    Write-Host "   Healthy: $healthy  Unhealthy: $unhealthy  Initial: $none" -ForegroundColor $(if ($healthy -eq 0) { "Red" } else { "Green" })
    foreach ($h in $health.TargetHealthDescriptions) {
        Write-Host "   - $($h.Target.Id): $($h.TargetHealth.State) $($h.TargetHealth.Reason)"
    }
    Write-Host ""
}

# 3. Recent logs
Write-Host "3. Recent app log (last 5 lines)" -ForegroundColor Yellow
try {
    $cmd4 = "aws logs tail /ecs/loan-engine-test --region $Region --since 10m"
    if ($profileArg) { $cmd4 = "aws $profileArg logs tail /ecs/loan-engine-test --region $Region --since 10m" }
    $log = cmd /c "$cmd4 2>&1" 2>&1 | Out-String
    if ($log) {
        ($log | Select-Object -Last 5) | ForEach-Object { Write-Host "   $_" }
    } else {
        Write-Host "   No recent log lines."
    }
} catch {
    Write-Host "   Could not fetch logs."
}
Write-Host ""

Write-Host "=== Next steps ===" -ForegroundColor Cyan
Write-Host "  - If runningCount=0 or targets Unhealthy: check logs above and README.md '503 Service Temporarily Unavailable'"
Write-Host "  - View full logs: aws logs tail /ecs/loan-engine-test --follow --region $Region"
Write-Host "  - Force new deployment: aws ecs update-service --cluster $ClusterName --service $ServiceName --force-new-deployment --region $Region"
if ($Profile) { Write-Host "  - Add --profile $Profile to aws commands if needed." }
Write-Host ""
