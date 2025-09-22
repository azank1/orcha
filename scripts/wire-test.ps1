param(
  [string]$Base = "http://localhost:8000"
)

function Post-Rpc($method, $params, $headers=@{}) {
  $body = @{ jsonrpc = "2.0"; id = [string](Get-Random); method = $method; params = $params } | ConvertTo-Json -Depth 10
  Invoke-WebRequest -Uri "$Base/rpc" -Method POST -ContentType 'application/json' -Headers $headers -Body $body
}

Write-Host "== Wire Test: P2A /rpc foodtec.* ==" -ForegroundColor Cyan

# 1) export_menu
$exp = Post-Rpc -method "foodtec.export_menu" -params @{ store_id = "default"; page = 1; page_size = 5 }
$expJson = $exp.Content | ConvertFrom-Json
$cats = $expJson.result.menu.categories | ForEach-Object { $_.name }
Write-Host "export_menu => status=$($exp.StatusCode) categories=$(($cats -join ', ')) total=$($expJson.result.total)" -ForegroundColor Green

# 2) validate_order
$draft = @{ items = @(@{ sku = "LARGE_PEP"; qty = 1 }) }
$val = Post-Rpc -method "foodtec.validate_order" -params $draft
$valJson = $val.Content | ConvertFrom-Json
Write-Host "validate_order => status=$($val.StatusCode) ok=$($valJson.result.ok) issues=$($valJson.result.issues)" -ForegroundColor Green

# 3) accept_order with idem
$idem = "wire-" + (Get-Random)
$acc = Post-Rpc -method "foodtec.accept_order" -params @{ draft = $draft; idem = $idem } -headers @{ 'Idempotency-Key' = $idem }
$accJson = $acc.Content | ConvertFrom-Json
Write-Host "accept_order => status=$($acc.StatusCode) ok=$($accJson.result.ok) order_id=$($accJson.result.order_id) idem=$($accJson.result.idem)" -ForegroundColor Green

# 3b) replay
$acc2 = Post-Rpc -method "foodtec.accept_order" -params @{ draft = $draft; idem = $idem } -headers @{ 'Idempotency-Key' = $idem }
$replay = $acc2.Headers['X-Idempotency-Replay']
Write-Host "accept_order (replay) => status=$($acc2.StatusCode) X-Idempotency-Replay=$replay" -ForegroundColor Yellow

Write-Host "== Done ==" -ForegroundColor Cyan
