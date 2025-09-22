param(
  [string]$McpBase = "http://localhost:9090"
)

function Invoke-Rpc($method, $params) {
  $body = @{ jsonrpc = "2.0"; id = [string](Get-Random); method = $method; params = $params } | ConvertTo-Json -Depth 10
  Invoke-WebRequest -Uri "$McpBase/rpc" -Method POST -ContentType 'application/json' -Body $body -UseBasicParsing
}

Write-Host "== MCP → Proxy → P2A wire test ==" -ForegroundColor Cyan

# export_menu
$exp = Invoke-Rpc -method 'foodtec.export_menu' -params @{ store_id = 'default' }
$expJ = $exp.Content | ConvertFrom-Json
$cats = $expJ.result.menu.categories | ForEach-Object { $_.name }
Write-Host "export_menu => status=$($exp.StatusCode) ok=$($expJ.result.ok) cats=$(($cats -join ', '))" -ForegroundColor Green

# validate
$draft = @{ items = @(@{ sku = 'LARGE_PEP'; qty = 1 }) }
$val = Invoke-Rpc -method 'foodtec.validate_order' -params $draft
$valJ = $val.Content | ConvertFrom-Json
Write-Host "validate_order => status=$($val.StatusCode) ok=$($valJ.result.ok)" -ForegroundColor Green

# accept + replay
$idem = "mcp-" + (Get-Random)
$acc = Invoke-Rpc -method 'foodtec.accept_order' -params @{ draft = $draft; idem = $idem }
$accJ = $acc.Content | ConvertFrom-Json
Write-Host "accept_order => status=$($acc.StatusCode) ok=$($accJ.result.ok) order_id=$($accJ.result.order_id) idem=$($accJ.result.idem)" -ForegroundColor Green
$acc2 = Invoke-Rpc -method 'foodtec.accept_order' -params @{ draft = $draft; idem = $idem }
# Headers on WebRequest for second call
$replay = $acc2.Headers['X-Idempotency-Replay']
Write-Host "accept_order (replay) => status=$($acc2.StatusCode) X-Idempotency-Replay=$replay" -ForegroundColor Yellow

Write-Host "== Done ==" -ForegroundColor Cyan
