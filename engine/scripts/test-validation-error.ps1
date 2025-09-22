# Auto-locate the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

Write-Host "🔍 Testing validation with wrong params ..."
$body = @{
    jsonrpc = "2.0"
    id      = "bad"
    method  = "menu.export"
    params  = @{ wrong_field = 123 }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://localhost:9090/rpc" -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 5