# Attach S3 access policy to the ECS task role for a given bucket.
# Use this when the app uses S3 (S3_BUCKET_NAME) but the task role was never given S3 permissions,
# or the bucket name changed.
# Usage: .\attach-s3-policy-to-task-role.ps1 -BucketName loan-engine-poc -Profile AWSAdministratorAccess-014148916722

param(
    [Parameter(Mandatory=$true)]
    [string]$BucketName,
    
    [Parameter(Mandatory=$false)]
    [string]$AppName = "loan-engine",
    
    [Parameter(Mandatory=$false)]
    [string]$Profile = ""
)

$ErrorActionPreference = "Stop"
$TaskRoleName = "ecsTaskRole-$AppName"

$bucketArn = "arn:aws:s3:::$BucketName"
$bucketPrefixArn = "arn:aws:s3:::$BucketName/*"
$s3Policy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Action = @("s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket")
            Resource = @($bucketPrefixArn)
        }
        @{
            Effect = "Allow"
            Action = @("s3:ListBucket")
            Resource = $bucketArn
        }
    )
} | ConvertTo-Json -Depth 10 -Compress

$s3PolicyFile = [System.IO.Path]::GetTempFileName()
try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($s3PolicyFile, $s3Policy, $utf8NoBom)
    
    $args = @("iam", "put-role-policy", "--role-name", $TaskRoleName, "--policy-name", "S3StoragePolicy", "--policy-document", "file://$s3PolicyFile")
    if (-not [string]::IsNullOrEmpty($Profile)) {
        $args = @("--profile", $Profile) + $args
    }
    & aws @args
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Attached S3 policy to $TaskRoleName for bucket: $BucketName" -ForegroundColor Green
    } else {
        Write-Host "Failed to attach policy. Ensure the role $TaskRoleName exists and you have IAM permissions." -ForegroundColor Red
        exit 1
    }
} finally {
    Remove-Item $s3PolicyFile -Force -ErrorAction SilentlyContinue
}
