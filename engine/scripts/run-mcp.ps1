# Auto-locate the project root based on script location
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

# Start MCP server
Write-Host "🚀 Starting MCP server on http://localhost:9090 ..."
npm run dev:mcp
