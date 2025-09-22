# Auto-locate the P2A root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$p2aRoot = Split-Path -Parent $scriptDir
Set-Location $p2aRoot

Write-Host "🔍 Testing P2A /healthz ..."
Invoke-RestMethod -Uri "http://localhost:8080/healthz" | ConvertTo-Json -Depth 5
