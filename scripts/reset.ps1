param(
  [int[]]$Ports = @(8080, 9090, 8000),
  [string[]]$Images = @("node.exe","npm.exe","python.exe","uvicorn.exe","ts-node.exe","webpack.exe")
)

Write-Host "[reset] Killing processes bound to ports: $($Ports -join ', ')" -ForegroundColor Yellow
foreach ($port in $Ports) {
  $pids = netstat -ano | findstr ":$port" | ForEach-Object { ($_ -split "\s+")[-1] } | Where-Object { ($_ -match '^[0-9]+$') -and ($_ -ne '0') } | Select-Object -Unique
  foreach ($procId in $pids) {
    try { taskkill /PID $procId /F | Out-Null } catch {}
  }
}

Write-Host "[reset] Killing common images: $($Images -join ', ')" -ForegroundColor Yellow
foreach ($img in $Images) {
  try { taskkill /IM $img /F | Out-Null } catch {}
}

# Best-effort: kill processes started from this repo path
$repo = Split-Path -Parent $PSCommandPath
Write-Host "[reset] Killing processes started from repo: $repo" -ForegroundColor Yellow
try {
  Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -and ($_.CommandLine -like "*$repo*") } |
    ForEach-Object { try { taskkill /PID $_.ProcessId /F | Out-Null } catch {} }
} catch {}

Write-Host "[reset] Done" -ForegroundColor Green

# Ensure success exit code
$global:LASTEXITCODE = 0

# Print port status summary
try {
  $portsStr = ($Ports | ForEach-Object { "$_=" + ((Test-NetConnection -ComputerName localhost -Port $_ -WarningAction SilentlyContinue).TcpTestSucceeded) }) -join ", "
  Write-Host "[reset] Port status: $portsStr" -ForegroundColor Green
} catch {}
