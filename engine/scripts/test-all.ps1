# Auto-locate the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

Write-Host "==============================" -ForegroundColor Cyan
Write-Host "🧪 MCP Step 2 Tests" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Cyan

Write-Host "`n[1/4] Health Check" -ForegroundColor Magenta
& .\scripts\test-health.ps1

Write-Host "`n[2/4] Tool Discovery" -ForegroundColor Magenta
& .\scripts\test-discovery.ps1

Write-Host "`n[3/4] Validation Error Test" -ForegroundColor Magenta
& .\scripts\test-validation-error.ps1

Write-Host "`n[4/4] Valid Request Test" -ForegroundColor Magenta
& .\scripts\test-valid-request.ps1

Write-Host "`n✅ All tests completed" -ForegroundColor Green