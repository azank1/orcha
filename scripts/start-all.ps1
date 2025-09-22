Write-Host "[start] Resetting ports 8000,8080,9090" -ForegroundColor Yellow
& "$PSScriptRoot\..\reset.ps1" -Ports @(8000,8080,9090) | Out-Null

Write-Host "[start] Starting P2A (8000)" -ForegroundColor Yellow
Start-Process -FilePath "$PSScriptRoot\..\P2A\.venv\Scripts\python.exe" -ArgumentList 'main.py' -WorkingDirectory "$PSScriptRoot\..\P2A" -WindowStyle Minimized

Write-Host "[start] Starting Proxy (8080)" -ForegroundColor Yellow
Start-Process -FilePath node -ArgumentList 'dist/index.js' -WorkingDirectory "$PSScriptRoot\..\engine\proxy" -WindowStyle Minimized

Write-Host "[start] Starting MCP (9090)" -ForegroundColor Yellow
Start-Process -FilePath node -ArgumentList 'dist/Index.js' -WorkingDirectory "$PSScriptRoot\..\engine\mcp_server" -WindowStyle Minimized

Start-Sleep -Seconds 2
Write-Host "[start] Health: " -NoNewline
$p8000 = (Test-NetConnection -ComputerName localhost -Port 8000).TcpTestSucceeded
$p8080 = (Test-NetConnection -ComputerName localhost -Port 8080).TcpTestSucceeded
$p9090 = (Test-NetConnection -ComputerName localhost -Port 9090).TcpTestSucceeded
Write-Host "8000=$p8000, 8080=$p8080, 9090=$p9090" -ForegroundColor Green
