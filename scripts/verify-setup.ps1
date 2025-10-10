# Quick Setup Verification
# Usage: .\scripts\verify-setup.ps1

Write-Host "🔍 Orcha-2 Setup Verification" -ForegroundColor Green

Write-Host "`n📂 Checking directory structure..." -ForegroundColor Yellow
$requiredDirs = @("orcha-2", "RP2A", "scripts")
$requiredFiles = @(".env", "README.md")

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "✅ $dir/" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $dir/" -ForegroundColor Red
    }
}

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $file" -ForegroundColor Red
    }
}

Write-Host "`n🐍 Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found" -ForegroundColor Red
}

Write-Host "`n📦 Checking key Python packages..." -ForegroundColor Yellow
$packages = @("fastapi", "uvicorn", "httpx", "pydantic", "rank-bm25")
foreach ($pkg in $packages) {
    try {
        python -c "import $pkg; print('✅ $pkg')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $pkg" -ForegroundColor Green
        } else {
            Write-Host "❌ $pkg (not installed)" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ $pkg (not installed)" -ForegroundColor Red
    }
}

Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. .\scripts\start-server.ps1    # Start backend"
Write-Host "  2. .\scripts\test-endpoints.ps1  # Test API"
Write-Host "  3. .\scripts\open-ui.ps1         # Open chat UI"
Write-Host "  4. .\scripts\test-full.ps1       # Full integration test"

Write-Host "`n📚 Architecture:" -ForegroundColor Cyan
Write-Host "  Browser → FastAPI → LLM (Ollama) → Menu Search → JSON Response"

Write-Host "`n✅ Setup verification complete!" -ForegroundColor Green