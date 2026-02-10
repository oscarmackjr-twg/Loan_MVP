# Database Initialization Script
# Run this after deployment to initialize the database schema and create admin user
# Usage: .\init-database.ps1 -Region us-east-1 -AppName loan-engine

param(
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$AppName = "loan-engine",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "test",
    
    [Parameter(Mandatory=$false)]
    [string]$Method = "local",  # "local", "ecs" (needs Session Manager plugin), or "ecs-task" (one-off task, no plugin)
    
    [Parameter(Mandatory=$false)]
    [switch]$SeedOnly = $false,  # If set, run only seed_admin.py (skip init_db). Use when tables exist and you only need to create/update admin.
    
    [Parameter(Mandatory=$false)]
    [string]$Profile = ""  # AWS CLI profile (e.g. for IAM Identity Center)
)

$ErrorActionPreference = "Stop"

function Write-Info { Write-Host "$args" -ForegroundColor Cyan }
function Write-Success { Write-Host "$args" -ForegroundColor Green }
function Write-Error { Write-Host "$args" -ForegroundColor Red }

# Get database connection string from Secrets Manager
Write-Info "Retrieving database credentials from Secrets Manager..."
if (-not [string]::IsNullOrEmpty($Profile)) {
    Write-Info "Using profile: $Profile. If you see SSO expired, run: aws sso login --profile $Profile"
}
$dbSecretName = "$AppName/$Environment/DATABASE_URL"
$secretCmd = "aws secretsmanager get-secret-value --secret-id $dbSecretName --region $Region --query SecretString --output text"
if (-not [string]::IsNullOrEmpty($Profile)) { $secretCmd = "aws --profile $Profile secretsmanager get-secret-value --secret-id $dbSecretName --region $Region --query SecretString --output text" }
try {
    $dbSecret = Invoke-Expression $secretCmd
    $dbSecret = "$dbSecret".Trim()
    if ([string]::IsNullOrEmpty($dbSecret) -or $dbSecret -match "SSO session|expired|invalid|error|Error") {
        Write-Error "Could not retrieve database URL. Response may be an error message."
        if ($dbSecret -match "SSO|expired") {
            Write-Error "Your SSO session has expired."
            Write-Error "Run: aws sso login --profile $Profile"
        } else {
            Write-Error "Ensure the secret exists and you have access: $dbSecretName"
        }
        exit 1
    }
    if ($dbSecret -notmatch "^postgresql://") {
        Write-Error "Secret does not look like a PostgreSQL URL. Check secret: $dbSecretName"
        exit 1
    }
    Write-Success "Retrieved database URL"
} catch {
    Write-Error "Failed to retrieve database secret: $dbSecretName"
    if ($_.Exception.Message -match "ResourceNotFoundException|can't find the specified secret") {
        Write-Host ""
        Write-Host "The secret was not found. It is created by deploy-aws.ps1 (step 6). If deploy failed before that, create it manually:" -ForegroundColor Yellow
        Write-Host "  1. Get your RDS master password (you set it during deploy, or reset it in RDS console)." -ForegroundColor Gray
        Write-Host "  2. Run:" -ForegroundColor Gray
        Write-Host "     .\deploy\aws\create-database-secret.ps1 -Region $Region -DBPassword 'YourRdsPassword' $(if($Profile){'-Profile '+$Profile})" -ForegroundColor Gray
        Write-Host "  Then run this script again." -ForegroundColor Gray
    }
    if (-not [string]::IsNullOrEmpty($Profile)) { Write-Error "Refresh SSO first if needed: aws sso login --profile $Profile" }
    exit 1
}

if ($Method -eq "local") {
    Write-Info "Initializing database from local machine..."
    
    # Check if psql is available (for validation)
    $psqlAvailable = Get-Command psql -ErrorAction SilentlyContinue
    if (-not $psqlAvailable) {
        Write-Info "Note: psql not found. Will use Python scripts only."
    }
    
    # Check Python is available
    $pythonAvailable = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonAvailable) {
        Write-Error "Python not found. Please install Python 3.10+ and ensure it's in your PATH."
        Write-Error "Or use -Method ecs to run initialization via ECS Exec."
        exit 1
    }
    
    # Set environment variable; RDS requires SSL, append sslmode=require if not present
    if ($dbSecret -match "\.rds\.amazonaws\.com" -and $dbSecret -notmatch "sslmode=") {
        if ($dbSecret -match "\?") { $dbSecret = $dbSecret + "&sslmode=require" } else { $dbSecret = $dbSecret + "?sslmode=require" }
        Write-Info "Using SSL for RDS connection (sslmode=require)"
    }
    $env:DATABASE_URL = $dbSecret
    
    # Change to backend directory
    $backendDir = Join-Path $PSScriptRoot "..\..\backend"
    if (-not (Test-Path $backendDir)) {
        Write-Error "Backend directory not found: $backendDir"
        exit 1
    }
    
    Push-Location $backendDir
    
    # Check if virtual environment exists or dependencies are installed
    Write-Info "Checking Python dependencies..."
    $venvPath = Join-Path $backendDir "venv"
    if (Test-Path $venvPath) {
        Write-Info "Activating virtual environment..."
        & "$venvPath\Scripts\Activate.ps1"
    } else {
        Write-Warning "Virtual environment not found. Install backend dependencies first:"
        Write-Host "  cd backend" -ForegroundColor Gray
        Write-Host "  python -m venv venv" -ForegroundColor Gray
        Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
        Write-Host "  pip install -r requirements.txt" -ForegroundColor Gray
        Write-Host "  cd ..\.." -ForegroundColor Gray
        Write-Host ""
        Write-Error "Then run this script again: .\deploy\aws\init-database.ps1 -Region us-east-1 -Profile AWSAdministratorAccess-014148916722"
        Pop-Location
        exit 1
    }
    
    try {
        if (-not $SeedOnly) {
            # Initialize database schema (run via cmd so Python stderr/tracebacks don't cause PowerShell to throw)
            Write-Info "Creating database tables..."
            $initOut = cmd /c "python scripts/init_db.py 2>&1" 2>&1 | Out-String
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Database initialization failed"
                if ($initOut) {
                    Write-Host ""
                    Write-Host "Error output:" -ForegroundColor Yellow
                    Write-Host $initOut -ForegroundColor Gray
                }
                if ($initOut -match "Connection timed out|10060|e3q8") {
                    Write-Host "Your machine cannot reach RDS (firewall or network). Options:" -ForegroundColor Yellow
                    Write-Host "  A. Run init from inside AWS (no RDS firewall change, no plugin):" -ForegroundColor White
                    Write-Host "     .\deploy\aws\init-database.ps1 -Region $Region -Method ecs-task$(if(-not [string]::IsNullOrEmpty($Profile)){" -Profile $Profile"})" -ForegroundColor Gray
                    Write-Host "  B. Or use -Method ecs (requires Session Manager plugin). Allow your IP:" -ForegroundColor White
                    Write-Host "     .\deploy\aws\allow-my-ip-rds.ps1 -Region $Region$(if(-not [string]::IsNullOrEmpty($Profile)){" -Profile $Profile"})" -ForegroundColor Gray
                    Write-Host "     Then RDS -> Databases -> loan-engine-test-db -> Modify -> Publicly accessible = Yes" -ForegroundColor Gray
                }
                if ($initOut -match "password authentication failed|SSL connection|sslmode|no pg_hba.conf") {
                    Write-Host "If RDS requires SSL, set DATABASE_URL with ?sslmode=require or use the RDS CA bundle. If password failed, ensure the secret loan-engine/test/DATABASE_URL has the correct password." -ForegroundColor Yellow
                }
                Write-Host ""
                exit 1
            }
            Write-Success "Database tables created"
        }
        
        # Create admin user (run via cmd so Python stderr doesn't cause PowerShell to throw)
        Write-Info "Creating admin user (seed_admin)..."
        $seedOut = cmd /c "python scripts/seed_admin.py 2>&1" 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Admin user creation failed"
            if ($seedOut) { Write-Host $seedOut -ForegroundColor Gray }
            exit 1
        }
        Write-Success "Admin user created"
        
        Write-Success "Database initialization complete!"
        Write-Info "Default credentials:"
        Write-Info "  Username: admin"
        Write-Info "  Password: admin123"
        Write-Info "  ⚠️  Change password after first login!"
        
    } finally {
        Pop-Location
    }
    
} elseif ($Method -eq "ecs") {
    Write-Info "Initializing database via ECS Exec (runs inside the app task; no need to open RDS to your IP)..."
    
    $ClusterName = "$AppName-$Environment"
    $ServiceName = "$AppName-$Environment"
    if (-not [string]::IsNullOrEmpty($Profile)) { Write-Info "Using profile: $Profile" }
    
    # Get running task (run via cmd so AWS stderr does not throw)
    Write-Info "Finding running ECS task..."
    $listCmd = "aws ecs list-tasks --cluster $ClusterName --service-name $ServiceName --region $Region --query taskArns[0] --output text"
    if (-not [string]::IsNullOrEmpty($Profile)) { $listCmd = "aws --profile $Profile ecs list-tasks --cluster $ClusterName --service-name $ServiceName --region $Region --query taskArns[0] --output text" }
    $taskArn = (cmd /c "$listCmd 2>&1" 2>&1 | Out-String).Trim()
    if (-not $taskArn -or $taskArn -eq "None") {
        Write-Error "No running tasks found for service $ServiceName. Ensure the ECS service is running and healthy."
        exit 1
    }
    
    $taskId = $taskArn | Split-Path -Leaf
    Write-Success "Found task: $taskId"
    
    Write-Info "Running database initialization inside task (requires ECS Exec enabled and SSM Session Manager plugin)..."
    $execCmd = "aws ecs execute-command --cluster $ClusterName --task $taskId --container app --command ""python scripts/init_db.py"" --interactive --region $Region 2>&1"
    if (-not [string]::IsNullOrEmpty($Profile)) { $execCmd = "aws --profile $Profile ecs execute-command --cluster $ClusterName --task $taskId --container app --command ""python scripts/init_db.py"" --interactive --region $Region 2>&1" }
    cmd /c $execCmd | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Database initialization failed. Ensure ECS Exec is enabled on the service."
        exit 1
    }
    
    Write-Info "Creating admin user..."
    $seedCmd = "aws ecs execute-command --cluster $ClusterName --task $taskId --container app --command ""python scripts/seed_admin.py"" --interactive --region $Region 2>&1"
    if (-not [string]::IsNullOrEmpty($Profile)) { $seedCmd = "aws --profile $Profile ecs execute-command --cluster $ClusterName --task $taskId --container app --command ""python scripts/seed_admin.py"" --interactive --region $Region 2>&1" }
    cmd /c $seedCmd | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Admin user creation failed"
        exit 1
    }
    
    Write-Success "Database initialization complete!"
    
} elseif ($Method -eq "ecs-task") {
    Write-Info "Initializing database via one-off ECS task (no Session Manager plugin required)..."
    
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
            $out = [System.IO.File]::ReadAllText($stdoutFile)
            $err = [System.IO.File]::ReadAllText($stderrFile)
            return @{ ExitCode = $p.ExitCode; Stdout = $out; Stderr = $err }
        } finally {
            Remove-Item $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue
        }
    }
    
    # Get current task definition and network config from the service
    Write-Info "Getting task definition and network config from service..."
    $r = Invoke-AwsEcs -ExtraArgs @("describe-services", "--cluster", $ClusterName, "--services", $ServiceName, "--query", "services[0].{taskDef:taskDefinition,netConfig:networkConfiguration}", "--output", "json")
    if ($r.ExitCode -ne 0) {
        Write-Error "Could not describe service $ServiceName. $($r.Stderr)"
        exit 1
    }
    $svc = $r.Stdout | ConvertFrom-Json
    $taskDef = $svc.taskDef
    if (-not $taskDef -or $taskDef -eq "None") {
        Write-Error "No task definition found for service $ServiceName"
        exit 1
    }
    $netConfig = $svc.netConfig
    if (-not $netConfig) {
        Write-Error "No network configuration found for service $ServiceName"
        exit 1
    }
    $subnets = ($netConfig.awsvpcConfiguration.subnets | ForEach-Object { $_ }) -join ","
    $secGroups = ($netConfig.awsvpcConfiguration.securityGroups | ForEach-Object { $_ }) -join ","
    $assignPublic = $netConfig.awsvpcConfiguration.assignPublicIp
    $netConfigStr = "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$secGroups],assignPublicIp=$assignPublic}"
    
    # Override container command. file:// on Windows fails with [Errno 22], so run aws via cmd with
    # JSON passed inline (quotes escaped for cmd; && escaped so cmd does not interpret it).
    $cmdScript = if ($SeedOnly) { "python scripts/seed_admin.py" } else { "python scripts/init_db.py && python scripts/seed_admin.py" }
    $cmdJson = $cmdScript -replace '\\', '\\\\' -replace '"', '\"'
    $overrides = "{`"containerOverrides`":[{`"name`":`"app`",`"command`":[`"/bin/sh`",`"-c`",`"$cmdJson`"]}]}"
    $overridesForCmd = $overrides -replace '"', '\"' -replace '&', '^&'
    $awsExe = (Get-Command aws -ErrorAction SilentlyContinue).Source
    if (-not $awsExe) { $awsExe = "aws" }
    # Use short path (8.3) so path with spaces (e.g. C:\Program Files) does not break cmd
    try {
        $fso = New-Object -ComObject Scripting.FileSystemObject
        $awsShort = $fso.GetFile($awsExe).ShortPath
    } catch {
        $awsShort = $awsExe
    }
    $runTaskArgs = "--cluster $ClusterName --task-definition $taskDef --launch-type FARGATE --network-configuration $netConfigStr --overrides `"$overridesForCmd`" --region $Region --query tasks[0].taskArn --output text"
    if ($Profile) { $runTaskArgs = "--profile $Profile $runTaskArgs" }
    
    Write-Info "Starting one-off task to run database initialization..."
    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    $cmdLine = "$awsShort ecs run-task $runTaskArgs"
    try {
        $p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "$cmdLine 2>`"$stderrFile`" 1>`"$stdoutFile`"" -Wait -NoNewWindow -PassThru
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
        Write-Error "No task ARN returned. $($r.Stdout) $($r.Stderr)"
        exit 1
    }
    $taskId = $taskArn | Split-Path -Leaf
    Write-Success "Started task: $taskId (waiting for it to finish)..."
    
    $r = Invoke-AwsEcs -ExtraArgs @("wait", "tasks-stopped", "--cluster", $ClusterName, "--tasks", $taskArn)
    if ($r.ExitCode -ne 0) {
        Write-Error "Task did not stop in time. Check ECS console for task $taskId"
        exit 1
    }
    
    $r = Invoke-AwsEcs -ExtraArgs @("describe-tasks", "--cluster", $ClusterName, "--tasks", $taskArn, "--query", "tasks[0].{stopCode:stopCode,stoppedReason:stoppedReason,containers:containers}", "--output", "json")
    if ($r.ExitCode -ne 0) {
        Write-Error "Could not describe task. $($r.Stderr)"
        exit 1
    }
    $taskObj = $r.Stdout | ConvertFrom-Json
    $appContainer = $taskObj.containers | Where-Object { $_.name -eq "app" } | Select-Object -First 1
    $exitCode = $appContainer.exitCode
    if ($null -eq $exitCode) { $exitCode = -1 }
    
    if ($exitCode -ne 0) {
        Write-Error "Database initialization failed (container exit code: $exitCode). Stopped reason: $($taskObj.stoppedReason)"
        $logStreamName = "ecs/app/$taskId"
        $logOutFile = [System.IO.Path]::GetTempFileName()
        $logErrFile = [System.IO.Path]::GetTempFileName()
        try {
            $logArgs = $profileArg + @("logs", "get-log-events", "--log-group-name", "/ecs/$AppName-$Environment", "--log-stream-name", $logStreamName, "--limit", "40", "--region", $Region, "--query", "events[*].message", "--output", "text")
            $p = Start-Process -FilePath "aws" -ArgumentList $logArgs -Wait -NoNewWindow -PassThru -RedirectStandardOutput $logOutFile -RedirectStandardError $logErrFile
            $logText = [System.IO.File]::ReadAllText($logOutFile)
            if ($logText) {
                Write-Host "`nLast log lines from task:" -ForegroundColor Yellow
                ($logText -split "`t" | Where-Object { $_.Trim() }) | Select-Object -Last 35 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            }
        } catch { }
        finally {
            Remove-Item $logOutFile, $logErrFile -Force -ErrorAction SilentlyContinue
        }
        Write-Host "`nFull logs: aws logs get-log-events --log-group-name /ecs/$AppName-$Environment --log-stream-name $logStreamName --region $Region $(if($Profile){'--profile '+$Profile})" -ForegroundColor Gray
        exit 1
    }
    
    Write-Success "Database initialization complete!"
    
} else {
    Write-Error "Invalid method: $Method. Use 'local', 'ecs', or 'ecs-task'"
    exit 1
}
