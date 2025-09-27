# One-command test runner for Windows PowerShell

Write-Host "Running All Tests" -ForegroundColor Green
Write-Host "===================="

# Test 1: P2A Direct API
Write-Host "[1] P2A Direct API Test..." -ForegroundColor Yellow
python test_smoke_p2a.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: P2A test failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2] Starting Proxy Server..." -ForegroundColor Yellow
$ProxyJob = Start-Job -ScriptBlock {
    Set-Location "D:\dev\orcha-1\proxy"
    python main.py
}

# Wait for server to start
Start-Sleep -Seconds 3

# Test 2: Proxy JSON-RPC
Write-Host "[3] Proxy JSON-RPC Test..." -ForegroundColor Yellow
python test_smoke_proxy.py
$ProxyTestResult = $LASTEXITCODE

# Clean up
Write-Host "[4] Stopping Proxy Server..." -ForegroundColor Yellow
Stop-Job $ProxyJob
Remove-Job $ProxyJob

if ($ProxyTestResult -ne 0) {
    Write-Host "FAIL: Proxy test failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "ALL TESTS PASSED" -ForegroundColor Green
Write-Host "PASS: P2A Direct API working" -ForegroundColor Green
Write-Host "PASS: Proxy JSON-RPC working" -ForegroundColor Green
Write-Host "PASS: End-to-end integration complete" -ForegroundColor Green