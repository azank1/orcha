# Start Orcha-2 Backend Server
# Usage: .\scripts\start-server.ps1

Write-Host "🚀 Starting Orcha-2 Automation Server..." -ForegroundColor Green

# Set environment variables
$env:USE_OLLAMA = "true"
$env:OLLAMA_HOST = "http://127.0.0.1:11434" 
$env:OLLAMA_MODEL = "llama3.2"
$env:USE_OPENAI = "false"
$env:PORT = "8000"

# Change to orcha-2 directory
Set-Location "orcha-2"

# Add current directory to Python path and start server
$env:PYTHONPATH = $PWD
Write-Host "Starting server on http://127.0.0.1:8000" -ForegroundColor Yellow

try {
    python -c "import sys; sys.path.insert(0, '.'); import uvicorn; uvicorn.run('automation.main:app', host='127.0.0.1', port=8000, reload=True)"
}
catch {
    Write-Host "❌ Error starting server: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure Python and required packages are installed" -ForegroundColor Yellow
}

# Return to original directory
Set-Location ".."