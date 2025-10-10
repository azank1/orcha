# Open Orcha-2 Chat UI
# Usage: .\scripts\open-ui.ps1

Write-Host "🖥️  Opening Orcha-2 Chat Interface..." -ForegroundColor Green

$uiPath = "orcha-2\automation\ui\chat.html"

if (Test-Path $uiPath) {
    Write-Host "Opening UI: $uiPath" -ForegroundColor Yellow
    Start-Process $uiPath
    Write-Host "`n✅ UI should open in your default browser" -ForegroundColor Green
    Write-Host "💡 Make sure the server is running (use .\scripts\start-server.ps1)" -ForegroundColor Cyan
} else {
    Write-Host "❌ UI file not found: $uiPath" -ForegroundColor Red
    Write-Host "Make sure you're running from the orcha-1 root directory" -ForegroundColor Yellow
}