# Verify Engine <-> P2A schema sync via SHA256 hashes
param(
    [string]$EngineDir = "$PSScriptRoot\..\engine\schemas\json",
    [string]$Manifest = "$PSScriptRoot\..\P2A\models\schemas_manifest.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host 'Schema Hash Check' -ForegroundColor Cyan
Write-Host "Engine JSON: $EngineDir" -ForegroundColor Gray
Write-Host "P2A Manifest: $Manifest" -ForegroundColor Gray

if (-not (Test-Path -Path $Manifest)) {
    Write-Host 'Manifest not found; run P2A schema export first: python P2A/scripts/export_schemas.py' -ForegroundColor Yellow
    exit 2
}

$manifestObj = Get-Content -Raw -Path $Manifest | ConvertFrom-Json
$entries = @($manifestObj.entries)
if (-not $entries) {
    Write-Host 'No entries found in manifest.' -ForegroundColor Red
    exit 1
}

$ok = $true
foreach ($e in $entries) {
    $src = Join-Path -Path $EngineDir -ChildPath $e.source
    if (-not (Test-Path -Path $src)) {
        Write-Host "Missing engine schema: $($e.source)" -ForegroundColor Red
        $ok = $false
        continue
    }
    $hash = Get-FileHash -Algorithm SHA256 -Path $src
    if ($hash.Hash -ne $e.source_sha256) {
        Write-Host "Hash mismatch: $($e.source)" -ForegroundColor Red
        Write-Host "   expected: $($e.source_sha256)" -ForegroundColor DarkGray
        Write-Host "   actual:   $($hash.Hash)" -ForegroundColor DarkGray
        $ok = $false
    } else {
        Write-Host "OK: $($e.source)" -ForegroundColor Green
    }
}

if ($ok) {
    Write-Host 'Schemas are in sync.' -ForegroundColor Green
    exit 0
}
else {
    Write-Host 'Schemas out of sync. Rebuild engine and re-export P2A models.' -ForegroundColor Yellow
    exit 3
}
