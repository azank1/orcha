Write-Host "[quickstart] Running setup" -ForegroundColor Cyan
& "$PSScriptRoot\setup.ps1"

Write-Host "[quickstart] Starting services" -ForegroundColor Cyan
& "$PSScriptRoot\start-all.ps1"

Write-Host "[quickstart] Running MCP → Proxy → P2A wire test" -ForegroundColor Cyan
& "$PSScriptRoot\test-mcp-wire.ps1"

Write-Host "[quickstart] Done" -ForegroundColor Green
