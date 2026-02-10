# Reset the app admin password by running reset_admin_password.py inside a one-off ECS task.
# Use this when you cannot reach RDS from your PC (connection timeout). No Session Manager plugin needed.
# Usage: .\reset-admin-password-ecs.ps1 -Region us-east-1 -Profile YourProfile [-Username admin] [-Password admin123]

param(
    [string]$Region = "us-east-1",
    [string]$Profile = "",
    [string]$AppName = "loan-engine",
    [string]$Environment = "test",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

$ErrorActionPreference = "Stop"
function Write-Info { Write-Host "$args" -ForegroundColor Cyan }
function Write-Success { Write-Host "$args" -ForegroundColor Green }
function Write-Error { Write-Host "$args" -ForegroundColor Red }

$ClusterName = "$AppName-$Environment"
$ServiceName = "$AppName-$Environment"
$profileArg = if ($Profile) { @("--profile", $Profile) } else { @() }

function Invoke-AwsEcs {
    param([string[]]$ExtraArgs)
    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    try {
        $allArgs = $profileArg + @("ecs") + $ExtraArgs + @("--region", $Region)
        $p = Start-Process -FilePath "aws" -ArgumentList $allArgs -Wait -NoNewWindow -PassThru -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile
        return @{ ExitCode = $p.ExitCode; Stdout = [System.IO.File]::ReadAllText($stdoutFile); Stderr = [System.IO.File]::ReadAllText($stderrFile) }
    } finally {
        Remove-Item $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Info "Resetting admin password via one-off ECS task (username: $Username)..."
Write-Info "Getting task definition and network config from service..."
$r = Invoke-AwsEcs -ExtraArgs @("describe-services", "--cluster", $ClusterName, "--services", $ServiceName, "--query", "services[0].{taskDef:taskDefinition,netConfig:networkConfiguration}", "--output", "json")
if ($r.ExitCode -ne 0) {
    Write-Error "Could not describe service. $($r.Stderr)"
    exit 1
}
$svc = $r.Stdout | ConvertFrom-Json
$taskDef = $svc.taskDef
if (-not $taskDef -or $taskDef -eq "None") {
    Write-Error "No task definition found for service $ServiceName"
    exit 1
}
$netConfig = $svc.netConfig
$subnets = ($netConfig.awsvpcConfiguration.subnets | ForEach-Object { $_ }) -join ","
$secGroups = ($netConfig.awsvpcConfiguration.securityGroups | ForEach-Object { $_ }) -join ","
$assignPublic = $netConfig.awsvpcConfiguration.assignPublicIp
$netConfigStr = "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$secGroups],assignPublicIp=$assignPublic}"

# Build container command; escape password single-quotes for shell
$passEscaped = $Password -replace "'", "'\\''"
$cmd = "python scripts/reset_admin_password.py --username $Username --password '$passEscaped'"
$cmdJsonEscaped = $cmd -replace '"', '\"'
$overrides = '{"containerOverrides":[{"name":"app","command":["/bin/sh","-c","' + $cmdJsonEscaped + '"]}]}'
$overridesForCmd = $overrides -replace '"', '\"' -replace '&', '^&'

$awsExe = (Get-Command aws -ErrorAction SilentlyContinue).Source
if (-not $awsExe) { $awsExe = "aws" }
try {
    $fso = New-Object -ComObject Scripting.FileSystemObject
    $awsShort = $fso.GetFile($awsExe).ShortPath
} catch {
    $awsShort = $awsExe
}
$runTaskArgs = "--cluster $ClusterName --task-definition $taskDef --launch-type FARGATE --network-configuration $netConfigStr --overrides `"$overridesForCmd`" --region $Region --query tasks[0].taskArn --output text"
if ($Profile) { $runTaskArgs = "--profile $Profile $runTaskArgs" }

$stdoutFile = [System.IO.Path]::GetTempFileName()
$stderrFile = [System.IO.Path]::GetTempFileName()
try {
    $p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "$awsShort ecs run-task $runTaskArgs 2>`"$stderrFile`" 1>`"$stdoutFile`"" -Wait -NoNewWindow -PassThru
    $r = @{ ExitCode = $p.ExitCode; Stdout = [System.IO.File]::ReadAllText($stdoutFile); Stderr = [System.IO.File]::ReadAllText($stderrFile) }
} finally {
    Remove-Item $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue
}
if ($r.ExitCode -ne 0) {
    Write-Error "Failed to run task. $($r.Stderr)"
    exit 1
}
$taskArn = $r.Stdout.Trim()
if (-not $taskArn -or $taskArn -eq "None") {
    Write-Error "No task ARN returned."
    exit 1
}
$taskId = $taskArn | Split-Path -Leaf
Write-Success "Started task: $taskId (waiting for it to finish)..."

$r = Invoke-AwsEcs -ExtraArgs @("wait", "tasks-stopped", "--cluster", $ClusterName, "--tasks", $taskArn)
if ($r.ExitCode -ne 0) {
    Write-Error "Task did not stop in time. Check ECS console for task $taskId"
    exit 1
}

$r = Invoke-AwsEcs -ExtraArgs @("describe-tasks", "--cluster", $ClusterName, "--tasks", $taskArn, "--query", "tasks[0].containers", "--output", "json")
$containers = $r.Stdout | ConvertFrom-Json
$appContainer = $containers | Where-Object { $_.name -eq "app" } | Select-Object -First 1
$exitCode = if ($appContainer.exitCode -ne $null) { [int]$appContainer.exitCode } else { -1 }
if ($exitCode -ne 0) {
    Write-Error "Password reset failed (container exit code: $exitCode)."
    $logStreamName = "ecs/app/$taskId"
    $logOutFile = [System.IO.Path]::GetTempFileName()
    $logErrFile = [System.IO.Path]::GetTempFileName()
    try {
        $logArgs = $profileArg + @("logs", "get-log-events", "--log-group-name", "/ecs/$AppName-$Environment", "--log-stream-name", $logStreamName, "--limit", "30", "--region", $Region, "--query", "events[*].message", "--output", "text")
        Start-Process -FilePath "aws" -ArgumentList $logArgs -Wait -NoNewWindow -RedirectStandardOutput $logOutFile -RedirectStandardError $logErrFile | Out-Null
        $logText = [System.IO.File]::ReadAllText($logOutFile)
        if ($logText) {
            Write-Host "`nLast log lines from task:" -ForegroundColor Yellow
            ($logText -split "`t" | Where-Object { $_.Trim() }) | Select-Object -Last 25 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        }
    } catch { }
    finally {
        Remove-Item $logOutFile, $logErrFile -Force -ErrorAction SilentlyContinue
    }
    Write-Host "`nFull logs: aws logs get-log-events --log-group-name /ecs/$AppName-$Environment --log-stream-name $logStreamName --region $Region $(if($Profile){'--profile '+$Profile})" -ForegroundColor Gray
    exit 1
}

Write-Success "Admin password reset successfully. Log in with username '$Username' and your new password."
