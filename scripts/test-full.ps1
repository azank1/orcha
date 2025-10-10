# Full Integration Test - Server + Endpoints + UI
# Usage: .\scripts\test-full.ps1

Write-Host "🚀 Orcha-2 Full Integration Test" -ForegroundColor Green

Write-Host "`n📋 Test Plan:" -ForegroundColor Cyan
Write-Host "  1. Start backend server in background"
Write-Host "  2. Wait for startup"
Write-Host "  3. Test all endpoints"
Write-Host "  4. Open UI for manual testing"
Write-Host "  5. Instructions for cleanup"

Write-Host "`nPress Enter to continue or Ctrl+C to cancel..." -ForegroundColor Yellow
Read-Host

# Start server in background
Write-Host "`n🟢 Starting server in background..." -ForegroundColor Green
$serverJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    .\scripts\start-server.ps1
}

# Wait for server to start
Write-Host "⏳ Waiting 10 seconds for server startup..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test endpoints
Write-Host "`n🧪 Testing endpoints..." -ForegroundColor Green
.\scripts\test-endpoints.ps1

# Open UI
Write-Host "`n🖥️  Opening UI..." -ForegroundColor Green
.\scripts\open-ui.ps1

Write-Host "`n✅ Integration test setup complete!" -ForegroundColor Green
Write-Host "`n📝 Manual UI Tests:" -ForegroundColor Cyan
Write-Host "   1. Type 'find pizza' - should show 3 pizza items"
Write-Host "   2. Type 'show me more' - should use same session"  
Write-Host "   3. Type 'I want to order pizza' - should show order intent"
Write-Host "   4. Check session ID in header"

Write-Host "`n🛑 To stop the server:" -ForegroundColor Red
Write-Host "   Run: Stop-Job $($serverJob.Id); Remove-Job $($serverJob.Id)"

Write-Host "`nServer Job ID: $($serverJob.Id)" -ForegroundColor Yellow