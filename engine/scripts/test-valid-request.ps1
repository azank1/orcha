# Auto-locate the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

Write-Host "🔍 Testing valid request from docs/examples/menu.export.req.json ..."
$body = Get-Content -Path "docs/examples/menu.export.req.json" -Raw
Invoke-RestMethod -Uri "http://localhost:9090/rpc" -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 5