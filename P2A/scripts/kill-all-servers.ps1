#!/usr/bin/env pwsh
# P2A Kill All Servers Script
# Kills all Python processes related to P2A servers

Write-Host "🛑 P2A Kill All Servers Script" -ForegroundColor Red
Write-Host "================================" -ForegroundColor Red

# Get all Python processes
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "🔍 Found Python processes:" -ForegroundColor Yellow
    
    $p2aProcesses = @()
    foreach ($process in $pythonProcesses) {
        try {
            $commandLine = $process.CommandLine
            if ($commandLine -like "*main.py*" -or $commandLine -like "*P2A*" -or $commandLine -like "*minimal_server*" -or $commandLine -like "*test_server*" -or $commandLine -like "*uvicorn*") {
                $p2aProcesses += $process
                Write-Host "   📋 PID $($process.Id): $commandLine" -ForegroundColor Cyan
            }
        } catch {
            # Some processes might not have CommandLine accessible
            Write-Host "   📋 PID $($process.Id): [Command line not accessible]" -ForegroundColor Gray
        }
    }
    
    if ($p2aProcesses.Count -gt 0) {
        Write-Host ""
        Write-Host "🛑 Killing $($p2aProcesses.Count) P2A-related process(es)..." -ForegroundColor Red
        
        foreach ($process in $p2aProcesses) {
            try {
                Stop-Process -Id $process.Id -Force
                Write-Host "   ✅ Killed PID $($process.Id)" -ForegroundColor Green
            } catch {
                Write-Host "   ❌ Failed to kill PID $($process.Id): $_" -ForegroundColor Red
            }
        }
        
        Write-Host ""
        Write-Host "🎯 All P2A servers have been terminated!" -ForegroundColor Green
        
    } else {
        Write-Host ""
        Write-Host "✅ No P2A-related Python processes found" -ForegroundColor Green
    }
} else {
    Write-Host "✅ No Python processes currently running" -ForegroundColor Green
}

# Additional cleanup - kill by port if needed
Write-Host ""
Write-Host "🔍 Checking for processes using common P2A ports..." -ForegroundColor Yellow

$ports = @(8000, 8001, 8080, 3000)
foreach ($port in $ports) {
    try {
        $netstat = netstat -ano | Select-String ":$port " | Select-String "LISTENING"
        if ($netstat) {
            foreach ($line in $netstat) {
                $pid = ($line -split '\s+')[-1]
                if ($pid -match '^\d+$') {
                    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($process) {
                        Write-Host "   🔌 Port $port used by PID $pid ($($process.ProcessName))" -ForegroundColor Cyan
                        try {
                            Stop-Process -Id $pid -Force
                            Write-Host "   ✅ Killed process using port $port" -ForegroundColor Green
                        } catch {
                            Write-Host "   ❌ Failed to kill process on port $port" -ForegroundColor Red
                        }
                    }
                }
            }
        }
    } catch {
        # Ignore errors when checking ports
    }
}

Write-Host ""
Write-Host "🧹 Server cleanup complete!" -ForegroundColor Green