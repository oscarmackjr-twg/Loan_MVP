# Loan Engine - Demo Script
# Use this to start backend and frontend, then verify connectivity and database.
# Run from project root: .\scripts\demo.ps1
#
# Option A: Start everything in separate terminals (recommended for demo)
#   Step 1: Open Terminal 1 -> .\scripts\start-backend.ps1
#   Step 2: Open Terminal 2 -> .\scripts\start-frontend.ps1
#   Step 3: Open Terminal 3 -> .\scripts\verify-demo.ps1
#   Step 4: Open browser to http://localhost:5173 and log in (admin / admin123)
#
# Option B: This script opens two new windows and then runs verification after a delay.
#   .\scripts\demo.ps1 -Launch

param(
    [switch]$Launch  # If set, start backend and frontend in new windows and run verify after delay
)

$ProjectRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
# If we're in scripts/, project root is parent
if ((Split-Path -Leaf $ProjectRoot) -eq "scripts") {
    $ProjectRoot = Split-Path -Parent $ProjectRoot
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Loan Engine - Demo" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Project root: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

if ($Launch) {
    Write-Host "Launching backend in new window..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; .\scripts\start-backend.ps1"
    Start-Sleep -Seconds 3
    Write-Host "Launching frontend in new window..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; .\scripts\start-frontend.ps1"
    Write-Host "Waiting 15 seconds for servers to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    Write-Host ""
    $VerifyScript = Join-Path $ProjectRoot "scripts\verify-demo.ps1"
    & $VerifyScript
    Write-Host "Open browser to: http://localhost:5173" -ForegroundColor Green
    Write-Host "Login: admin / admin123" -ForegroundColor Green
    exit 0
}

# No -Launch: print instructions
Write-Host "DEMO STEPS (run in separate terminals):" -ForegroundColor White
Write-Host ""
Write-Host "  Terminal 1 - Backend:" -ForegroundColor Cyan
Write-Host "    cd $ProjectRoot" -ForegroundColor Gray
Write-Host "    .\scripts\start-backend.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  Terminal 2 - Frontend:" -ForegroundColor Cyan
Write-Host "    cd $ProjectRoot" -ForegroundColor Gray
Write-Host "    .\scripts\start-frontend.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  Terminal 3 - Verify connectivity & database:" -ForegroundColor Cyan
Write-Host "    cd $ProjectRoot" -ForegroundColor Gray
Write-Host "    .\scripts\verify-demo.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "  Browser:" -ForegroundColor Cyan
Write-Host "    http://localhost:5173   (login: admin / admin123)" -ForegroundColor Gray
Write-Host ""
Write-Host "Or run with -Launch to start backend and frontend in new windows:" -ForegroundColor Yellow
Write-Host "  .\scripts\demo.ps1 -Launch" -ForegroundColor Gray
Write-Host ""
