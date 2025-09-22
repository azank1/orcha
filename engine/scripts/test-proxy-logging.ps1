# Auto-locate the project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

Write-Host "🧪 Testing Proxy Structured Logging" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Define test order
$body = @{
  items = @(
    @{
      sku = "PIZZA_TEST"
      qty = 2
    }
  )
} | ConvertTo-Json

# Generate custom request ID
$requestId = "test-req-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$idemKey = "test-idem-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Write-Host "`n1️⃣ Sending request with custom request ID: $requestId" -ForegroundColor Yellow

try {
    # Make request with custom request ID
    $response = Invoke-WebRequest -Uri "http://localhost:8080/apiclient/acceptOrder" `
        -Method Post `
        -Body $body `
        -ContentType "application/json" `
        -Headers @{ 
            "X-Request-ID" = $requestId
            "Idempotency-Key" = $idemKey
        }
    
    # Extract the request ID from the response header
    $returnedRequestId = $response.Headers["X-Request-ID"]
    
    # Verify the request ID was preserved
    if ($returnedRequestId -eq $requestId) {
        Write-Host "✅ Request ID preserved correctly: $returnedRequestId" -ForegroundColor Green
    } else {
        Write-Host "❌ Request ID mismatch! Sent: $requestId, Got: $returnedRequestId" -ForegroundColor Red
    }
    
    Write-Host "`nResponse Headers:" -ForegroundColor Blue
    $response.Headers | Format-Table -AutoSize
    
    Write-Host "`nResponse Body:" -ForegroundColor Blue
    $responseContent = $response.Content | ConvertFrom-Json
    $responseContent | ConvertTo-Json
    
    Write-Host "`n2️⃣ Checking logs in console output" -ForegroundColor Yellow
    Write-Host "Please verify that the logs in the proxy console contain:" -ForegroundColor Yellow
    Write-Host " - JSON-structured log entries" -ForegroundColor Yellow
    Write-Host " - The request ID: $requestId" -ForegroundColor Yellow
    Write-Host " - Request and response timing information" -ForegroundColor Yellow
    Write-Host " - Order acceptance details" -ForegroundColor Yellow
}
catch {
    Write-Host "❌ Test failed with exception" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}