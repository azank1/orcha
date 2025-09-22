# Auto-locate the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

Write-Host "🧪 Testing proxy idempotency and replay functionality..." -ForegroundColor Cyan

# Generate a unique test identifier
$testId = "test-" + [guid]::NewGuid().ToString().Substring(0, 8)
Write-Host "Using test ID: $testId" -ForegroundColor Gray

# Define the order payload
$orderPayload = @{
    items = @(
        @{
            sku = "LARGE_PEP"
            qty = 1
        }
    )
} | ConvertTo-Json

Write-Host "`n[1/3] First order request with idempotency key..." -ForegroundColor Magenta
$firstResponse = $null

try {
    $firstResponse = Invoke-RestMethod -Uri "http://localhost:8080/apiclient/acceptOrder" `
        -Method Post `
        -Body $orderPayload `
        -ContentType "application/json" `
        -Headers @{ "Idempotency-Key" = $testId }
    
    Write-Host "✅ First request successful!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Blue
    $firstResponse | ConvertTo-Json -Depth 3
} 
catch {
    Write-Host "❌ First request failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n[2/3] Second request with same idempotency key (should be replayed)..." -ForegroundColor Magenta
$replayResponse = $null
$replayHeaders = $null

try {
    $replayRequest = Invoke-WebRequest -Uri "http://localhost:8080/apiclient/acceptOrder" `
        -Method Post `
        -Body $orderPayload `
        -ContentType "application/json" `
        -Headers @{ "Idempotency-Key" = $testId }
    
    $replayResponse = $replayRequest.Content | ConvertFrom-Json
    $replayHeaders = $replayRequest.Headers
    
    Write-Host "✅ Replay request successful!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Blue
    $replayResponse | ConvertTo-Json -Depth 3
    
    Write-Host "Headers:" -ForegroundColor Blue
    $replayHeaders | Format-List
} 
catch {
    Write-Host "❌ Replay request failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n[3/3] Validating replay behavior..." -ForegroundColor Magenta

# Check if responses match
$responsesMatch = ($firstResponse.order_id -eq $replayResponse.order_id)
if ($responsesMatch) {
    Write-Host "✅ Responses match! Same order_id returned: $($firstResponse.order_id)" -ForegroundColor Green
} else {
    Write-Host "❌ Responses don't match! First: $($firstResponse.order_id), Replay: $($replayResponse.order_id)" -ForegroundColor Red
}

# Check for replay header
if ($replayHeaders.Contains("X-Idempotent-Replayed")) {
    Write-Host "✅ X-Idempotent-Replayed header present: $($replayHeaders["X-Idempotent-Replayed"])" -ForegroundColor Green
} else {
    Write-Host "❌ X-Idempotent-Replayed header missing" -ForegroundColor Red
}

# Overall test result
if ($responsesMatch -and $replayHeaders.Contains("X-Idempotent-Replayed")) {
    Write-Host "`n✨ Idempotency test PASSED! The proxy correctly replays identical responses." -ForegroundColor Green
} else {
    Write-Host "`n❌ Idempotency test FAILED! The proxy doesn't properly replay responses." -ForegroundColor Red
}