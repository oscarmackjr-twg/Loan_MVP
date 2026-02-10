# Start Loan Engine Frontend
# Run from project root: .\scripts\start-frontend.ps1
# Or from frontend: ..\scripts\start-frontend.ps1

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path "$ProjectRoot\frontend")) {
    $ProjectRoot = Split-Path -Parent $ProjectRoot
}
$FrontendDir = Join-Path $ProjectRoot "frontend"

if (-not (Test-Path $FrontendDir)) {
    Write-Host "Frontend directory not found: $FrontendDir" -ForegroundColor Red
    exit 1
}

Write-Host "Starting Loan Engine Frontend..." -ForegroundColor Cyan
Write-Host "  Directory: $FrontendDir" -ForegroundColor Gray
Write-Host "  URL:       http://localhost:5173" -ForegroundColor Gray
Write-Host "  API:       http://localhost:8000 (ensure backend is running)" -ForegroundColor Gray
Write-Host ""

Set-Location $FrontendDir

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies (npm install)..." -ForegroundColor Yellow
    npm install
}

npm run dev
