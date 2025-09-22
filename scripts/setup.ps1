param(
  [switch]$Force
)

Write-Host "[setup] Preparing Orcha-1 workspace" -ForegroundColor Cyan

# Python venv + dependencies
Push-Location "$PSScriptRoot\..\P2A"
if ($Force -and (Test-Path .venv)) { Remove-Item -Recurse -Force .venv }
if (-not (Test-Path .venv)) {
  Write-Host "[setup] Creating Python venv" -ForegroundColor Yellow
  python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
Write-Host "[setup] Installing Python packages" -ForegroundColor Yellow
pip install -r requirements.txt
Pop-Location

# Node deps + build for Proxy and MCP
foreach ($proj in @("engine/proxy","engine/mcp_server")) {
  Push-Location "$PSScriptRoot\..\$proj"
  if (-not (Test-Path node_modules)) {
    Write-Host "[setup] npm ci in $proj" -ForegroundColor Yellow
    npm ci
  }
  Write-Host "[setup] building $proj" -ForegroundColor Yellow
  npm run build
  Pop-Location
}

Write-Host "[setup] Done" -ForegroundColor Green
