# Run script for the engine directory
# Auto-locate the project root based on script location
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

function Write-Status {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$Color = "White"
    )
    
    Write-Host $Message -ForegroundColor $Color
}

Write-Status "Engine - Service Management" "Cyan"
Write-Status "==========================" "Cyan"
Write-Status "1. Start Proxy Server" "White"
Write-Status "2. Start MCP Server" "White"
Write-Status "3. Run Tests" "White"
Write-Status "4. Start Both Services" "White"
Write-Status "0. Exit" "White"

$choice = Read-Host "`nSelect an option (0-4)"

switch ($choice) {
    "1" {
        Write-Status "`n🚀 Starting Proxy server on http://localhost:8080 ..." "Yellow"
        Set-Location -Path "$projectRoot\proxy"
        npm start
    }
    "2" {
        Write-Status "`n🚀 Starting MCP server on http://localhost:9090 ..." "Yellow"
        Set-Location -Path "$projectRoot\mcp_server"
        npm run dev:mcp
    }
    "3" {
        Write-Status "`n🧪 Running tests..." "Yellow"
        $testDir = "$projectRoot\scripts"
        Set-Location -Path $testDir
        .\run-proxy-tests.ps1
    }
    "4" {
        Write-Status "`n🚀 Starting both services..." "Yellow"
        Write-Status "Starting Proxy server in background..." "White"
        
        # Start proxy in background
        $proxyJob = Start-Job -ScriptBlock {
            Set-Location -Path "$using:projectRoot\proxy"
            npm start
        }
        
        # Give proxy time to start
        Start-Sleep -Seconds 3
        
        # Start MCP server
        Write-Status "Starting MCP server..." "White"
        Set-Location -Path "$projectRoot\mcp_server"
        npm run dev:mcp
        
        # Clean up background job if MCP server exits
        if (Get-Job -Id $proxyJob.Id -ErrorAction SilentlyContinue) {
            Stop-Job -Id $proxyJob.Id
            Remove-Job -Id $proxyJob.Id
        }
    }
    "0" {
        Write-Status "Exiting..." "Yellow"
        exit 0
    }
    default {
        Write-Status "Invalid selection. Exiting." "Red"
        exit 1
    }
}