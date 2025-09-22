# Auto-locate the P2A root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$p2aRoot = Split-Path -Parent $scriptDir
Set-Location $p2aRoot

Write-Host "🔍 Testing P2A /.well-known/mcp/tools ..."
Write-Host "[menu]" -ForegroundColor Cyan
Invoke-RestMethod -Uri "http://localhost:8080/menu/.well-known/mcp/tools" | ConvertTo-Json -Depth 6
Write-Host "[order]" -ForegroundColor Cyan
Invoke-RestMethod -Uri "http://localhost:8080/order/.well-known/mcp/tools" | ConvertTo-Json -Depth 6
