param(
  [string]$Base = "http://localhost:8000",
  [switch]$StartServer
)

function Invoke-Rpc($method, $params, $headers=@{}) {
  $body = @{ jsonrpc = "2.0"; id = [string](Get-Random); method = $method; params = $params } | ConvertTo-Json -Depth 10
  Invoke-WebRequest -Uri "$Base/rpc" -Method POST -ContentType 'application/json' -Headers $headers -Body $body -UseBasicParsing
}

if ($StartServer) {
  Write-Host "[test] Starting P2A (mock) in background..." -ForegroundColor Yellow
  Start-Process -FilePath 'D:/dev/orcha-1/P2A/.venv/Scripts/python.exe' -ArgumentList 'main.py' -WorkingDirectory 'd:\dev\orcha-1\P2A' -WindowStyle Minimized
  Start-Sleep -Seconds 2
}

Write-Host "== P2A MOCK /rpc smoke ==" -ForegroundColor Cyan

# export_menu defaults page=1, page_size=50
$exp = Invoke-Rpc -method 'foodtec.export_menu' -params @{ store_id = 'default' }
$expJson = $exp.Content | ConvertFrom-Json
$cats = $expJson.result.menu.categories | ForEach-Object { $_.name }
Write-Host "export_menu => status=$($exp.StatusCode) page=$($expJson.result.page) page_size=$($expJson.result.page_size) total=$($expJson.result.total) cats=$(($cats -join ', '))" -ForegroundColor Green

# validate_order
$draft = @{ items = @(@{ sku = 'LARGE_PEP'; qty = 1 }) }
$val = Invoke-Rpc -method 'foodtec.validate_order' -params $draft
$valJson = $val.Content | ConvertFrom-Json
Write-Host "validate_order => status=$($val.StatusCode) ok=$($valJson.result.ok)" -ForegroundColor Green

# accept_order + replay
$idem = "mock-" + (Get-Random)
$acc = Invoke-Rpc -method 'foodtec.accept_order' -params @{ draft = $draft; idem = $idem } -headers @{ 'Idempotency-Key' = $idem }
$accJson = $acc.Content | ConvertFrom-Json
Write-Host "accept_order => status=$($acc.StatusCode) ok=$($accJson.result.ok) order_id=$($accJson.result.order_id) idem=$($accJson.result.idem)" -ForegroundColor Green
$acc2 = Invoke-Rpc -method 'foodtec.accept_order' -params @{ draft = $draft; idem = $idem } -headers @{ 'Idempotency-Key' = $idem }
$replay = $acc2.Headers['X-Idempotency-Replay']
Write-Host "accept_order (replay) => status=$($acc2.StatusCode) X-Idempotency-Replay=$replay" -ForegroundColor Yellow

Write-Host "== Done ==" -ForegroundColor Cyan
