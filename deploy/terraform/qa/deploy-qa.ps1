# Deploy Loan Engine QA with Terraform (optionally build and push Docker image)
# Run from repo root: .\deploy\terraform\qa\deploy-qa.ps1
# Or from deploy/terraform/qa: ..\..\..\deploy\terraform\qa\deploy-qa.ps1 (then PushImage from repo root)

param(
    [string]$Region = "us-east-1",
    [string]$Profile = "",
    [switch]$PushImage = $false,
    [switch]$AutoApprove = $false
)

$ErrorActionPreference = "Stop"
$qaDir = $PSScriptRoot
$repoRoot = (Resolve-Path (Join-Path $qaDir "..\..\..")).Path
if (-not (Test-Path (Join-Path $repoRoot "deploy\terraform\qa\main.tf"))) {
    $repoRoot = (Get-Location).Path
}

# Ensure we're in QA Terraform directory for init/plan/apply
Push-Location $qaDir
try {
    if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
        Write-Error "Terraform not found. Install Terraform and ensure it is on PATH."
        exit 1
    }

    # Database password for QA
    if (-not $env:TF_VAR_db_password) {
        $env:TF_VAR_db_password = "Intrepid456$%"
        Write-Host "Set TF_VAR_db_password to QA default (Intrepid456`$%). Override with `$env:TF_VAR_db_password = '...'" -ForegroundColor Cyan
    }

    $tfArgs = @("-var", "aws_region=$Region")
    if ($Profile) {
        $env:AWS_PROFILE = $Profile
        Write-Host "Using AWS profile: $Profile" -ForegroundColor Cyan
    }

    Write-Host "Terraform init..." -ForegroundColor Cyan
    terraform init
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "Terraform plan..." -ForegroundColor Cyan
    terraform plan @tfArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    if ($AutoApprove) {
        terraform apply -auto-approve @tfArgs
    } else {
        terraform apply @tfArgs
    }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    if ($PushImage) {
        Pop-Location
        $repoUrl = (terraform -chdir=$qaDir output -raw ecr_repository_url 2>$null)
        if (-not $repoUrl) {
            Write-Warning "Could not get ecr_repository_url from Terraform output. Push image manually."
            exit 0
        }
        $repoHost = ($repoUrl -split "/")[0]
        Write-Host "Logging into ECR and building/pushing image..." -ForegroundColor Cyan
        $env:AWS_DEFAULT_REGION = $Region
        $awsCli = @("--region", $Region)
        if ($Profile) { $awsCli += @("--profile", $Profile) }
        & aws ecr get-login-password @awsCli | docker login --username AWS --password-stdin $repoHost
        if ($LASTEXITCODE -ne 0) { Write-Error "ECR login failed."; exit 1 }
        docker build -f (Join-Path $repoRoot "deploy\Dockerfile") -t "${repoUrl}:latest" $repoRoot
        if ($LASTEXITCODE -ne 0) { Write-Error "Docker build failed."; exit 1 }
        docker push "${repoUrl}:latest"
        if ($LASTEXITCODE -ne 0) { Write-Error "Docker push failed."; exit 1 }
        Write-Host "Forcing ECS service to deploy new image..." -ForegroundColor Cyan
        $ecsArgs = @("ecs", "update-service", "--cluster", "loan-engine-qa", "--service", "loan-engine-qa", "--force-new-deployment", "--region", $Region)
        if ($Profile) { $ecsArgs = @("--profile", $Profile) + $ecsArgs }
        & aws @ecsArgs
        Push-Location $qaDir
    }
} finally {
    Pop-Location -ErrorAction SilentlyContinue
}

$url = (terraform -chdir=$qaDir output -raw application_url 2>$null)
Write-Host ""
Write-Host "QA deployment complete. Application URL: $url" -ForegroundColor Green
Write-Host "Allow 2-5 minutes for ECS to become healthy, then initialize the database (migrations + seed)." -ForegroundColor Yellow
