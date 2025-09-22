# Auto-locate the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

function Write-SectionHeader {
    param([string]$text)
    Write-Host "`n=================================================" -ForegroundColor Cyan
    Write-Host " $text" -ForegroundColor Cyan
    Write-Host "=================================================" -ForegroundColor Cyan
}

Write-SectionHeader "ORCHA PROXY TEST SUITE"

# Check if proxy is running
try {
    $null = Invoke-WebRequest -Uri "http://localhost:8080/healthz" -Method Head -TimeoutSec 2
    $proxyRunning = $true
    Write-Host "✅ Proxy server detected at http://localhost:8080" -ForegroundColor Green
}
catch {
    $proxyRunning = $false
    Write-Host "❌ Proxy server not detected at http://localhost:8080" -ForegroundColor Red
    Write-Host "Please start the proxy server before running tests." -ForegroundColor Yellow
    Write-Host "Run: cd proxy && npm start" -ForegroundColor Yellow
    exit 1
}

# Display test menu
Write-Host "`nAvailable Tests:" -ForegroundColor Yellow
Write-Host "1. Health Endpoint Test" -ForegroundColor White
Write-Host "2. Idempotency Test" -ForegroundColor White
Write-Host "3. Structured Logging Test" -ForegroundColor White
Write-Host "4. Run All Tests" -ForegroundColor White
Write-Host "0. Exit" -ForegroundColor White

$choice = Read-Host "`nSelect a test to run (0-4)"

switch ($choice) {
    "1" {
        Write-SectionHeader "RUNNING HEALTH ENDPOINT TEST"
        & "$projectRoot\scripts\test-proxy-health.ps1"
    }
    "2" {
        Write-SectionHeader "RUNNING IDEMPOTENCY TEST"
        & "$projectRoot\scripts\test-proxy-idempotency.ps1"
    }
    "3" {
        Write-SectionHeader "RUNNING STRUCTURED LOGGING TEST"
        & "$projectRoot\scripts\test-proxy-logging.ps1"
    }
    "4" {
        Write-SectionHeader "RUNNING ALL PROXY TESTS"
        
        Write-SectionHeader "1. HEALTH ENDPOINT TEST"
        & "$projectRoot\scripts\test-proxy-health.ps1"
        
        Write-SectionHeader "2. IDEMPOTENCY TEST"
        & "$projectRoot\scripts\test-proxy-idempotency.ps1"
        
        Write-SectionHeader "3. STRUCTURED LOGGING TEST"
        & "$projectRoot\scripts\test-proxy-logging.ps1"
        
        Write-SectionHeader "TEST SUITE COMPLETE"
    }
    "0" {
        Write-Host "Exiting test runner." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "Invalid selection. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host "`nTests completed. Check results above for any failures." -ForegroundColor Cyan