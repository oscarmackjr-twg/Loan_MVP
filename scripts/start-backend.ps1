# Start Loan Engine Backend
# Run from project root: .\scripts\start-backend.ps1
# Or from backend: ..\scripts\start-backend.ps1

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path "$ProjectRoot\backend")) {
    $ProjectRoot = Split-Path -Parent $ProjectRoot
}
$BackendDir = Join-Path $ProjectRoot "backend"

if (-not (Test-Path $BackendDir)) {
    Write-Host "Backend directory not found: $BackendDir" -ForegroundColor Red
    exit 1
}

Write-Host "Starting Loan Engine Backend..." -ForegroundColor Cyan
Write-Host "  Directory: $BackendDir" -ForegroundColor Gray
Write-Host "  URL:       http://localhost:8000" -ForegroundColor Gray
Write-Host "  Docs:      http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""

Set-Location $BackendDir

# Use uvicorn (same as README)
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
