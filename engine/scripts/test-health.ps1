# Auto-locate the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

Write-Host "🔍 Testing /healthz ..."
Invoke-RestMethod -Uri "http://localhost:9090/healthz" | ConvertTo-Json -Depth 5