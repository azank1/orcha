Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Resolve repo root
$repoRoot = Split-Path -Parent $PSScriptRoot
Write-Host "Repo Root: $repoRoot" -ForegroundColor DarkGray

function Invoke-TestSection($title, [scriptblock]$action) {
  Write-Host "`n====================================" -ForegroundColor Cyan
  Write-Host "🧪 $title" -ForegroundColor Green
  Write-Host "====================================" -ForegroundColor Cyan
  & $action
}

# 1) Engine tests require MCP server at 9090; assume user has it running.
Invoke-TestSection "Engine Tests" {
  Push-Location "$repoRoot\engine\scripts"
  try {
    & .\test-health.ps1
    & .\test-discovery.ps1
    if (Test-Path .\test-validation-error.ps1) { & .\test-validation-error.ps1 }
    if (Test-Path .\test-valid-request.ps1) { & .\test-valid-request.ps1 }
  } finally { Pop-Location }
}

# 2) P2A tests assume app running at 8080; minimal health + discovery
Invoke-TestSection "P2A Tests" {
  Push-Location "$repoRoot\P2A\scripts"
  try {
    if (Test-Path .\test-health.ps1) { & .\test-health.ps1 }
    if (Test-Path .\test-discovery.ps1) { & .\test-discovery.ps1 }
  } finally { Pop-Location }
}

Write-Host "`n✅ All test sections completed." -ForegroundColor Green
