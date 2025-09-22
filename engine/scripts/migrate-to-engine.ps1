# Migration script to copy files from orcha-1 to engine
# This script preserves the directory structure and handles migration gracefully

# Function to display status messages with color
function Write-Status {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$Color = "White"
    )
    
    Write-Host $Message -ForegroundColor $Color
}

# Set up paths
$sourcePath = "D:\dev\orcha-1\orcha-1"
$destinationPath = "D:\dev\orcha-1\engine"

Write-Status "Starting migration from orcha-1 to engine..." "Cyan"
Write-Status "Source: $sourcePath" "Cyan"
Write-Status "Destination: $destinationPath" "Cyan"
Write-Status "--------------------------------------------" "Cyan"

# Ensure destination directory exists
if (-not (Test-Path -Path $destinationPath)) {
    Write-Status "Creating destination directory: $destinationPath" "Yellow"
    New-Item -ItemType Directory -Path $destinationPath | Out-Null
}

# Copy files with progress
Write-Status "Copying files and directories..." "Cyan"

# Get list of items to copy (excluding .git directory)
$items = Get-ChildItem -Path $sourcePath -Exclude ".git"
$totalItems = $items.Count
$currentItem = 0

foreach ($item in $items) {
    $currentItem++
    $percentComplete = [math]::Round(($currentItem / $totalItems) * 100)
    
    Write-Progress -Activity "Copying files" -Status "$percentComplete% Complete" -PercentComplete $percentComplete -CurrentOperation $item.Name
    
    $targetPath = Join-Path -Path $destinationPath -ChildPath $item.Name
    
    if ($item.PSIsContainer) {
        # It's a directory
        Write-Status "  Copying directory: $($item.Name)" "White"
        Copy-Item -Path $item.FullName -Destination $targetPath -Recurse -Force
    } else {
        # It's a file
        Write-Status "  Copying file: $($item.Name)" "White"
        Copy-Item -Path $item.FullName -Destination $targetPath -Force
    }
}

Write-Progress -Activity "Copying files" -Completed

# Verify migration
$sourceCount = (Get-ChildItem -Path $sourcePath -Recurse | Where-Object { -not $_.PSIsContainer }).Count
$destCount = (Get-ChildItem -Path $destinationPath -Recurse | Where-Object { -not $_.PSIsContainer }).Count

Write-Status "`nMigration Complete!" "Green"
Write-Status "--------------------------------------------" "Cyan"
Write-Status "Files in source: $sourceCount" "White"
Write-Status "Files in destination: $destCount" "White"

if ($sourceCount -eq $destCount) {
    Write-Status "✅ All files copied successfully!" "Green"
} else {
    Write-Status "⚠️ File count mismatch! Some files may not have been copied." "Yellow"
}

Write-Status "`nNext Steps:" "Cyan"
Write-Status "1. Verify the engine directory contains all necessary files" "White"
Write-Status "2. Test the application from the new directory" "White"
Write-Status "3. Update any remaining path references if needed" "White"