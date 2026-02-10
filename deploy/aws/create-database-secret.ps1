# Create or update the DATABASE_URL secret in Secrets Manager. RDS requires SSL (sslmode=require).
# Use this if the secret is missing, or to fix wrong password / add SSL after "password authentication failed" or "no encryption".
# If you don't know the RDS password, reset it: RDS -> loan-engine-test-db -> Modify -> Master password.
# Usage: .\create-database-secret.ps1 -Region us-east-1 -Profile YourProfile -DBPassword "YourRDSMasterPassword"

param(
    [string]$Region = "us-east-1",
    [string]$Profile = "",
    [string]$AppName = "loan-engine",
    [string]$Environment = "test",
    [Parameter(Mandatory=$true)]
    [string]$DBPassword,
    [string]$DBUsername = "postgres",
    [string]$DBName = "loan_engine"
)

$ErrorActionPreference = "Stop"
$profileArg = if ($Profile) { @("--profile", $Profile) } else { @() }

Write-Host "Creating secret $AppName/$Environment/DATABASE_URL from RDS..." -ForegroundColor Cyan

$DBInstanceIdentifier = "$AppName-$Environment-db"
$descArgs = @($profileArg + @("rds", "describe-db-instances", "--db-instance-identifier", $DBInstanceIdentifier, "--region", $Region, "--query", "DBInstances[0].Endpoint.Address", "--output", "text")) | Where-Object { $null -ne $_ -and $_ -ne "" }
$outFile = [System.IO.Path]::GetTempFileName()
$errFile = [System.IO.Path]::GetTempFileName()
try {
    $p = Start-Process -FilePath "aws" -ArgumentList $descArgs -Wait -NoNewWindow -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
    $endpoint = [System.IO.File]::ReadAllText($outFile).Trim()
} finally {
    Remove-Item $outFile, $errFile -Force -ErrorAction SilentlyContinue
}
if (-not $endpoint -or $endpoint -eq "None") {
    Write-Error "Could not find RDS instance: $DBInstanceIdentifier. Is it created and in region $Region?"
    exit 1
}

# Build URL without double-quoting password (avoids ! and other chars breaking); RDS requires SSL
$databaseUrl = "postgresql://" + $DBUsername + ":" + [string]$DBPassword + "@" + $endpoint + ":5432/" + $DBName + "?sslmode=require"
if ([string]::IsNullOrEmpty($databaseUrl)) {
    Write-Error "DATABASE_URL is empty (check RDS endpoint and password)."
    exit 1
}
$secretName = "$AppName/$Environment/DATABASE_URL"

function Invoke-AwsSecret {
    param([string[]]$AwsArgs)
    $clean = @($AwsArgs | Where-Object { $null -ne $_ -and $_ -ne "" })
    $o = [System.IO.Path]::GetTempFileName()
    $e = [System.IO.Path]::GetTempFileName()
    try {
        $p = Start-Process -FilePath "aws" -ArgumentList $clean -Wait -NoNewWindow -PassThru -RedirectStandardOutput $o -RedirectStandardError $e
        return @{ ExitCode = $p.ExitCode; Stderr = [System.IO.File]::ReadAllText($e) }
    } finally {
        Remove-Item $o, $e -Force -ErrorAction SilentlyContinue
    }
}

# Create or update secret (update if it already exists)
$createArgs = @($profileArg + @("secretsmanager", "create-secret", "--name", $secretName, "--secret-string", $databaseUrl, "--region", $Region)) | Where-Object { $null -ne $_ -and $_ -ne "" }
$r = Invoke-AwsSecret -AwsArgs $createArgs
if ($r.ExitCode -eq 0) {
    Write-Host "Created secret: $secretName" -ForegroundColor Green
} else {
    $updateArgs = @($profileArg + @("secretsmanager", "update-secret", "--secret-id", $secretName, "--secret-string", $databaseUrl, "--region", $Region)) | Where-Object { $null -ne $_ -and $_ -ne "" }
    $r = Invoke-AwsSecret -AwsArgs $updateArgs
    if ($r.ExitCode -ne 0) {
        Write-Error "Failed to update secret. $($r.Stderr)"
        exit 1
    }
    Write-Host "Updated secret: $secretName (password and sslmode=require)" -ForegroundColor Green
}
Write-Host "Force new ECS deployment so tasks use the new secret: aws ecs update-service --cluster $AppName-$Environment --service $AppName-$Environment --force-new-deployment --region $Region $(if($Profile){'--profile '+$Profile})" -ForegroundColor Gray
Write-Host "Then run init-database: .\init-database.ps1 -Region $Region -Method ecs-task $(if($Profile){'-Profile '+$Profile})" -ForegroundColor Gray
