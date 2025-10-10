# Orcha-2 Phase 2: Unified Test Runner
# PowerShell script to run all available Phase 2 tests with clear output and exit code
# Usage:
#   pwsh -File .\run_all.ps1
#   # or in Windows PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\run_all.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Force UTF-8 to avoid UnicodeEncodeError in Windows PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

function Write-Section($title) {
  Write-Host "`n$('-' * 70)" -ForegroundColor DarkGray
  Write-Host "==> $title" -ForegroundColor Cyan
  Write-Host $('-' * 70) -ForegroundColor DarkGray
}

function Run-Step($name, $scriptBlock) {
  Write-Section $name
  $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    & $scriptBlock
    $stopwatch.Stop()
    Write-Host ("PASS {0}: {1}s" -f ${name}, [math]::Round($stopwatch.Elapsed.TotalSeconds,2)) -ForegroundColor Green
    return $true
  } catch {
    $stopwatch.Stop()
    Write-Host ("FAIL {0}: {1}s" -f ${name}, [math]::Round($stopwatch.Elapsed.TotalSeconds,2)) -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ScriptStackTrace) { Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed }
    return $false
  }
}

$repoRoot = (Resolve-Path "$PSScriptRoot\..\").Path
$mcpDir   = (Resolve-Path "$PSScriptRoot\..\mcp").Path
$testsDir = $PSScriptRoot

Write-Host "ORCHA-2 PHASE 2: Unified Test Runner" -ForegroundColor Yellow
Write-Host ("Repo: {0}" -f $repoRoot)
Write-Host ("Date: {0}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))

$results = @{}

# 1) Environment quick check
$results['Environment'] = Run-Step 'Environment & Python' {
  Write-Host "Python: " -NoNewline; python --version
  Write-Host "Pip:    " -NoNewline; pip --version
}

# 2) MCP: verify_phase2
$results['MCP Verify'] = Run-Step 'MCP Verify Phase 2' {
  Push-Location $mcpDir
  try {
    python "$testsDir\verify_phase2.py"
    if ($LASTEXITCODE -ne 0) { throw "verify_phase2.py exited with code $LASTEXITCODE" }
  } finally {
    Pop-Location
  }
}

# 3) MCP: integration
$results['MCP Integration'] = Run-Step 'MCP Integration (adapters + tools)' {
  Push-Location $mcpDir
  try {
    python "$testsDir\test_phase2_integration.py"
    if ($LASTEXITCODE -ne 0) { throw "test_phase2_integration.py exited with code $LASTEXITCODE" }
  } finally {
    Pop-Location
  }
}

# 4) MCP: complete validation
$results['MCP Complete'] = Run-Step 'MCP Complete Validation' {
  Push-Location $mcpDir
  try {
    python "$testsDir\test_complete_phase2.py"
    if ($LASTEXITCODE -ne 0) { throw "test_complete_phase2.py exited with code $LASTEXITCODE" }
  } finally {
    Pop-Location
  }
}

# 5) Proxy (optional): only if legacy proxy exists at repo root
$proxyRoot = Join-Path $repoRoot 'proxy'
$proxyReq = Join-Path $proxyRoot 'requirements.txt'
$proxySmoke = Join-Path $repoRoot 'tests\test_smoke_proxy.py'
$proxyRunner = Join-Path $proxyRoot 'smoke_proxy.py'
if ((Test-Path $proxyRoot) -and (Test-Path $proxyReq) -and (Test-Path $proxySmoke) -and (Test-Path $proxyRunner)) {
  $results['Proxy Smoke'] = Run-Step 'Proxy Smoke Tests' {
    Push-Location $repoRoot
    try {
      pip install -r "$proxyRoot\requirements.txt"
      if ($LASTEXITCODE -ne 0) { throw "pip install failed with code $LASTEXITCODE" }
      python ".\tests\test_smoke_proxy.py"
      if ($LASTEXITCODE -ne 0) { throw "test_smoke_proxy.py exited with code $LASTEXITCODE" }
      python ".\proxy\smoke_proxy.py"
      if ($LASTEXITCODE -ne 0) { throw "smoke_proxy.py exited with code $LASTEXITCODE" }
    } finally {
      Pop-Location
    }
  }
} else {
  Write-Host "Proxy tests: SKIPPED (missing files in \proxy)" -ForegroundColor DarkYellow
  $results['Proxy Smoke'] = $null
}

# 6) P2A (optional): only if P2A exists
$p2aRoot = Join-Path $repoRoot 'P2A'
$p2aReq = Join-Path $p2aRoot 'requirements.txt'
$p2aSmoke = Join-Path $repoRoot 'tests\test_smoke_p2a.py'
if ((Test-Path $p2aRoot) -and (Test-Path $p2aReq) -and (Test-Path $p2aSmoke)) {
  $results['P2A Smoke'] = Run-Step 'P2A Smoke Tests' {
    Push-Location $repoRoot
    try {
      pip install -r "$p2aRoot\requirements.txt"
      if ($LASTEXITCODE -ne 0) { throw "pip install failed with code $LASTEXITCODE" }
      python ".\tests\test_smoke_p2a.py"
      if ($LASTEXITCODE -ne 0) { throw "test_smoke_p2a.py exited with code $LASTEXITCODE" }
    } finally {
      Pop-Location
    }
  }
} else {
  Write-Host "P2A tests: SKIPPED (missing files in \P2A)" -ForegroundColor DarkYellow
  $results['P2A Smoke'] = $null
}

# Summary
Write-Section 'SUMMARY'
$passed = 0; $failed = 0; $skipped = 0
foreach ($k in $results.Keys) {
  $v = $results[$k]
  if ($v -eq $true) { $passed++ ; Write-Host ("  PASS {0}" -f $k) -ForegroundColor Green }
  elseif ($v -eq $false) { $failed++ ; Write-Host ("  FAIL {0}" -f $k) -ForegroundColor Red }
  else { $skipped++ ; Write-Host ("  SKIP {0}" -f $k) -ForegroundColor DarkYellow }
}

Write-Host "`nResults: Passed=$passed  Failed=$failed  Skipped=$skipped"

if ($failed -gt 0) {
  Write-Host "`nOne or more steps failed" -ForegroundColor Red
  exit 1
} else {
  Write-Host "`nAll available tests passed" -ForegroundColor Green
  exit 0
}
