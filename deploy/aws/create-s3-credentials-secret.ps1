# Create or update S3 credentials secret in AWS Secrets Manager
# Usage: .\create-s3-credentials-secret.ps1 -Region us-east-1 -BucketName my-bucket -AccessKeyId AKIA... -SecretKey wJalr...

param(
    [string]$Region = "us-east-1",
    [string]$Profile = "",
    [string]$AppName = "loan-engine",
    [string]$Environment = "test",
    [Parameter(Mandatory=$true)]
    [string]$BucketName,
    [Parameter(Mandatory=$true)]
    [string]$AccessKeyId,
    [Parameter(Mandatory=$true)]
    [string]$SecretKey
)

$ErrorActionPreference = "Stop"
$profileArg = if ($Profile) { @("--profile", $Profile) } else { @() }

Write-Host "Creating S3 credentials secret..." -ForegroundColor Cyan

$secretName = "$AppName/$Environment/S3_CREDENTIALS"

# Build JSON secret value
$secretValue = @{
    bucket_name = $BucketName
    region = $Region
    access_key_id = $AccessKeyId
    secret_access_key = $SecretKey
} | ConvertTo-Json -Compress

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

# Create or update secret
$createArgs = @($profileArg + @("secretsmanager", "create-secret", "--name", $secretName, "--secret-string", $secretValue, "--region", $Region)) | Where-Object { $null -ne $_ -and $_ -ne "" }
$r = Invoke-AwsSecret -AwsArgs $createArgs
if ($r.ExitCode -eq 0) {
    Write-Host "Created secret: $secretName" -ForegroundColor Green
} else {
    $updateArgs = @($profileArg + @("secretsmanager", "update-secret", "--secret-id", $secretName, "--secret-string", $secretValue, "--region", $Region)) | Where-Object { $null -ne $_ -and $_ -ne "" }
    $r = Invoke-AwsSecret -AwsArgs $updateArgs
    if ($r.ExitCode -eq 0) {
        Write-Host "Updated secret: $secretName" -ForegroundColor Green
    } else {
        Write-Error "Failed to create/update secret. $($r.Stderr)"
        exit 1
    }
}

Write-Host ""
Write-Host "Secret created: $secretName" -ForegroundColor Green
Write-Host "To use in ECS, reference this secret in your task definition environment variables." -ForegroundColor Gray
