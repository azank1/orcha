# Auto-locate the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

Write-Host "🧪 Testing proxy health endpoint..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/healthz" -Method Get
    
    Write-Host "✅ Health check successful!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Blue
    $response | ConvertTo-Json -Depth 3
    
    # Validate response fields
    $requiredFields = @("ok", "ts", "service", "version")
    $missingFields = $requiredFields | Where-Object { -not $response.PSObject.Properties.Name.Contains($_) }
    
    if ($missingFields.Count -eq 0) {
        Write-Host "✅ Health response contains all required fields" -ForegroundColor Green
    } else {
        Write-Host "❌ Health response missing fields: $($missingFields -join ', ')" -ForegroundColor Red
    }
    
    # Validate ok is true
    if ($response.ok -eq $true) {
        Write-Host "✅ Health status is OK" -ForegroundColor Green
    } else {
        Write-Host "❌ Health status is NOT OK" -ForegroundColor Red
    }
} 
catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
}