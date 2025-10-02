$ErrorActionPreference = "Stop"

function PostJson($url, $body) {
  Invoke-RestMethod -Uri $url -Method POST -ContentType "application/json" -Body ($body | ConvertTo-Json -Depth 12)
}

Write-Host "=== Testing Order Acceptance Flow ===" -ForegroundColor Cyan

Write-Host "[1/3] Validating order..." -ForegroundColor Yellow
$ext = "ext-test-" + [int](Get-Date -UFormat %s)
$validate = PostJson "http://127.0.0.1:8080/rpc" @{
  jsonrpc="2.0"
  id="v1"
  method="foodtec.validate_order"
  params=@{
    category="Appetizer"
    item="3pcs Chicken Strips w/ FF"
    size="Lg"
    price=6.99
    customer=@{ name="Test User"; phone="410-555-1234" }
  }
}

if (-not $validate.result) {
  throw "Validation failed"
}

$canon = [double]$validate.result.canonical_price
Write-Host "Validation successful: canonicalPrice = $canon" -ForegroundColor Green

if ($canon -lt 6.99) {
  throw "Bad canonical price: $canon"
}

Write-Host "[2/3] Accepting order..." -ForegroundColor Yellow
$accept = PostJson "http://127.0.0.1:8080/rpc" @{
  jsonrpc="2.0"
  id="a1"
  method="foodtec.accept_order"
  params=@{
    category="Appetizer"
    item="3pcs Chicken Strips w/ FF"
    size="Lg"
    customer=@{ name="Test User"; phone="410-555-1234" }
    menuPrice=6.99
    canonicalPrice=$canon
    externalRef=$ext
    idem="acc-test-" + [int](Get-Date -UFormat %s)
  }
}

if ($accept.error) {
  throw "Accept failed: $($accept.error.message)"
}

if (-not $accept.result.success) {
  throw "Accept failed"
}

Write-Host "Acceptance successful with canonicalPrice=$canon" -ForegroundColor Green

Write-Host "[3/3] Verifying order data..." -ForegroundColor Yellow
$orderData = $accept.result.data
if ($orderData) {
  Write-Host "  Order ID: $($orderData.id)" -ForegroundColor Gray
  Write-Host "  Promise Time: $($orderData.promiseTime)" -ForegroundColor Gray
  Write-Host "  Final Price: $($orderData.price)" -ForegroundColor Gray
}

Write-Host "=== All Tests Passed ===" -ForegroundColor Green
