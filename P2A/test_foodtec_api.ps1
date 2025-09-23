# Step 3.A - Manual FoodTec API Testing Script
# Test the exact request format being sent by our implementation

$base = "https://pizzabolis-lab.foodtecsolutions.com/ws/store/v1"
$path = "/menu/categories" 
$user = "apiclient"
$pass = "Tn2dtS6n4u5eVYk"  # FOODTEC_MENU_PASS

# Create Basic Auth header
$credentials = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("$user`:$pass"))
$headers = @{
    "Authorization" = "Basic $credentials"
    "Accept" = "application/json"
}

# Test 1: CORRECT request with orderType (the actual fix!)
Write-Host "=== Test 1: CORRECT request with orderType ==="
$url1 = "$base$path" + "?orderType=Pickup"
Write-Host "URL: $url1"

try {
    $response1 = Invoke-RestMethod -Uri $url1 -Method GET -Headers $headers -ErrorAction Stop
    Write-Host "🎉 SUCCESS: Got JSON response"
    Write-Host "Categories found: $($response1.Count)"
    Write-Host "First category: $($response1[0].category)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "FAILED: Status $statusCode - $($_.Exception.Message)"
}

# Test 2: Request with pagination parameters  
Write-Host "`n=== Test 2: Request with pagination ==="
$url2 = "$base$path" + "?orderType=Pickup&page=1&pageSize=10"
Write-Host "URL: $url2"

try {
    $response2 = Invoke-RestMethod -Uri $url2 -Method GET -Headers $headers -ErrorAction Stop
    Write-Host "🎉 SUCCESS: Got JSON response"
    Write-Host "Categories found: $($response2.Count)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "FAILED: Status $statusCode - $($_.Exception.Message)"
}

# Test 3: Request without store_id (maybe it's inferred from subdomain)
Write-Host "`n=== Test 3: Request without store_id ==="
$url3 = "$base$path"
Write-Host "URL: $url3"

try {
    $response3 = Invoke-RestMethod -Uri $url3 -Method GET -Headers $headers -ErrorAction Stop
    Write-Host "SUCCESS: Got JSON response"
    Write-Host "Categories found: $($response3.categories.Count)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "FAILED: Status $statusCode - $($_.Exception.Message)"
}

# Test 4: Different store_id values
Write-Host "`n=== Test 4: Different store_id values ==="
$storeIds = @("default", "store_123", "1", "pizzabolis")

foreach ($storeId in $storeIds) {
    $url4 = "$base$path?store_id=$storeId"
    Write-Host "Testing store_id=$storeId"
    
    try {
        $response4 = Invoke-RestMethod -Uri $url4 -Method GET -Authentication Basic -Credential (New-Object PSCredential($user, (ConvertTo-SecureString $pass -AsPlainText -Force))) -ErrorAction Stop
        Write-Host "  SUCCESS: Got JSON response"
        Write-Host "  Categories found: $($response4.categories.Count)"
        break  # Stop on first success
    } catch {
        Write-Host "  FAILED: Status $($_.Exception.Response.StatusCode)"
    }
}

Write-Host "`n=== Summary ==="
Write-Host "If all tests failed with 400, the issue is likely:"
Write-Host "1. Parameter name mismatch (store_id vs storeId vs store vs id)"
Write-Host "2. Missing required headers (Content-Type, Accept, etc.)"
Write-Host "3. API expects POST with JSON body instead of GET with query params"
Write-Host "4. Different authentication method required"
Write-Host "`nCheck the FoodTec API documentation for exact specification."