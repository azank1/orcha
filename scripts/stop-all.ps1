Write-Host "[stop] Stopping services on 8000,8080,9090" -ForegroundColor Yellow
& "$PSScriptRoot\..\reset.ps1" -Ports @(8000,8080,9090) | Out-Null
Write-Host "[stop] Done" -ForegroundColor Green
