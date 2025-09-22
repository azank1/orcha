# Auto-locate the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

Write-Host "🔍 Testing /.well-known/mcp/tools ..."
Invoke-RestMethod -Uri "http://localhost:9090/.well-known/mcp/tools" | ConvertTo-Json -Depth 5