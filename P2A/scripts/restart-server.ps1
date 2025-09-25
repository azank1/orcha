#!/usr/bin/env pwsh
# P2A Server Restart Script
# Restarts the FoodTec P2A JSON-RPC Server

Write-Host "🔄 P2A Server Restart Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Kill any existing Python processes for P2A
Write-Host "🛑 Killing existing P2A servers..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*main.py*" -or $_.CommandLine -like "*P2A*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Wait a moment for cleanup
Start-Sleep -Seconds 2

# Change to P2A directory
Set-Location $PSScriptRoot\..

Write-Host "📁 Working directory: $(Get-Location)" -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "🐍 Activating Python virtual environment..." -ForegroundColor Green
    & ".venv\Scripts\Activate.ps1"
} else {
    Write-Warning "⚠️  Virtual environment not found at .venv\Scripts\Activate.ps1"
}

# Start the server
Write-Host "🚀 Starting P2A FoodTec Server..." -ForegroundColor Green
Write-Host "   📡 Server will run on: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "   🔍 JSON-RPC endpoint: http://127.0.0.1:8000/rpc" -ForegroundColor Cyan
Write-Host "   📋 Available methods:" -ForegroundColor Cyan
Write-Host "      - foodtec.export_menu" -ForegroundColor White
Write-Host "      - foodtec.validate_order" -ForegroundColor White
Write-Host "      - foodtec.accept_order" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    python main.py
} catch {
    Write-Error "❌ Failed to start server: $_"
    exit 1
}