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
Write-Host "[4] Starting MCP Server..." -ForegroundColor Yellow
$McpJob = Start-Job -ScriptBlock {
    Set-Location "D:\dev\orcha-1\MCP"
    node dist/index.js
}

# Wait for MCP server to start
Start-Sleep -Seconds 3

# Test 3: MCP E2E Test
Write-Host "[5] MCP E2E Test..." -ForegroundColor Yellow
Set-Location "D:\dev\orcha-1\MCP"
npx ts-node MCP_tests/test-all-tools.ts
$McpTestResult = $LASTEXITCODE
Set-Location "D:\dev\orcha-1\tests"

# Clean up
Write-Host "[6] Stopping MCP Server..." -ForegroundColor Yellow
Stop-Job $McpJob
Remove-Job $McpJob

Write-Host "[7] Stopping Proxy Server..." -ForegroundColor Yellow
Stop-Job $ProxyJob
Remove-Job $ProxyJob

if ($ProxyTestResult -ne 0) {
    Write-Host "FAIL: Proxy test failed" -ForegroundColor Red
    exit 1
}

if ($McpTestResult -ne 0) {
    Write-Host "FAIL: MCP test failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "ALL TESTS PASSED" -ForegroundColor Green
Write-Host "PASS: P2A Direct API working" -ForegroundColor Green
Write-Host "PASS: Proxy JSON-RPC working" -ForegroundColor Green
Write-Host "PASS: MCP E2E integration working" -ForegroundColor Green
Write-Host "PASS: End-to-end integration complete" -ForegroundColor Green