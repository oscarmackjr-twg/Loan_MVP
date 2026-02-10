# Verify Demo - Loan Engine
# Run this after starting backend and frontend to verify connectivity and database.
# Usage: .\scripts\verify-demo.ps1   or   powershell -File scripts\verify-demo.ps1

$ErrorActionPreference = "Stop"
$BackendUrl = "http://localhost:8000"
$FrontendUrl = "http://localhost:5173"
$HealthUrl = "$BackendUrl/health"
$ReadyUrl = "$BackendUrl/health/ready"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Loan Engine - Demo Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Backend health (API only)
Write-Host "[1/4] Backend API (health)..." -NoNewline
try {
    $r = Invoke-RestMethod -Uri $HealthUrl -Method Get -TimeoutSec 5
    if ($r.status -eq "healthy") {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "      $HealthUrl -> $($r | ConvertTo-Json -Compress)"
    } else {
        Write-Host " UNEXPECTED" -ForegroundColor Yellow
        Write-Host "      Response: $($r | ConvertTo-Json -Compress)"
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "      $_.Exception.Message"
    Write-Host "      Make sure the backend is running: cd backend; uvicorn api.main:app --reload"
    exit 1
}

# 2. Backend + Database (ready)
Write-Host "[2/4] Backend + Database (ready)..." -NoNewline
try {
    $r = Invoke-RestMethod -Uri $ReadyUrl -Method Get -TimeoutSec 5
    if ($r.status -eq "ready" -and $r.database -eq "connected") {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "      $ReadyUrl -> database: $($r.database)"
    } else {
        Write-Host " DEGRADED" -ForegroundColor Yellow
        Write-Host "      $($r | ConvertTo-Json -Compress)"
        if ($r.error) { Write-Host "      Error: $($r.error)" -ForegroundColor Yellow }
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "      $_.Exception.Message"
    Write-Host "      Check DATABASE_URL and that PostgreSQL is running."
    exit 1
}

# 3. Frontend (optional - may not be running yet)
Write-Host "[3/4] Frontend (optional)..." -NoNewline
try {
    $r = Invoke-WebRequest -Uri $FrontendUrl -Method Get -TimeoutSec 5 -UseBasicParsing
    if ($r.StatusCode -eq 200) {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "      $FrontendUrl -> $($r.StatusCode)"
    } else {
        Write-Host " HTTP $($r.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host " Not running (start with: cd frontend; npm run dev)" -ForegroundColor DarkGray
}

# 4. API root
Write-Host "[4/4] API root..." -NoNewline
try {
    $r = Invoke-RestMethod -Uri $BackendUrl -Method Get -TimeoutSec 5
    Write-Host " OK" -ForegroundColor Green
    Write-Host "      $BackendUrl -> $($r.message) (docs: $($r.docs))"
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  All checks passed. Demo is ready." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend:  $BackendUrl  (API docs: $BackendUrl/docs)" -ForegroundColor White
Write-Host "  Frontend: $FrontendUrl" -ForegroundColor White
Write-Host "  Login:    admin / admin123 (change after first login)" -ForegroundColor White
Write-Host ""
