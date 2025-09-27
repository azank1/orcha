# FoodTec JSON-RPC Proxy Server

Minimal JSON-RPC proxy server for FoodTec API integration.

## Quick Start

### 1. Setup Environment
```powershell
# Copy environment template and add your FoodTec credentials
copy P2A\.env.template P2A\.env
# Edit P2A\.env with your credentials
```

### 2. Install Dependencies
```powershell
cd P2A
pip install -r requirements.txt
cd ..\proxy  
pip install -r requirements.txt
cd ..
```

### 3. Run Complete Test Suite (Automated)
```powershell
cd tests
.\run_all.ps1
```
**This script automatically:**
- Starts the proxy server on port 8080
- Tests all endpoints (health, menu export, validation, acceptance)
- Shows request/response details for each test
- Stops the server when done

### 4. Start Server Manually (For Manual Testing)
```powershell
cd proxy
python main.py
# Server runs on http://127.0.0.1:8080
```

## Manual API Testing

### Health Check
**PowerShell:**
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8080/healthz" -Method GET
```

### 1. Menu Export
**PowerShell:**
```powershell
$menuBody = '{"jsonrpc":"2.0","id":"menu-001","method":"foodtec.export_menu","params":{"order_type":"D"}}'
Invoke-WebRequest -Uri "http://127.0.0.1:8080/rpc" -Method POST -Body $menuBody -ContentType "application/json"
```

### 2. Order Validation
**PowerShell:**
```powershell
$validateBody = '{"jsonrpc":"2.0","id":"validate-001","method":"foodtec.validate_order","params":{"phone":"410-555-1234","category":"Appetizer","item_name":"3pcs Chicken Strips w/ FF","size_name":"Lg","original_price":6.99,"external_ref":"test-ref-123"}}'
Invoke-WebRequest -Uri "http://127.0.0.1:8080/rpc" -Method POST -Body $validateBody -ContentType "application/json"
```

### 3. Order Acceptance
**PowerShell:**
```powershell
$acceptBody = '{"jsonrpc":"2.0","id":"accept-001","method":"foodtec.accept_order","params":{"phone":"410-555-1234","category":"Appetizer","item_name":"3pcs Chicken Strips w/ FF","size_name":"Lg","canonical_price":7.41,"external_ref":"test-ref-456"}}'
Invoke-WebRequest -Uri "http://127.0.0.1:8080/rpc" -Method POST -Body $acceptBody -ContentType "application/json"
```

## Test Direct P2A (Bypass Proxy)
```powershell
cd P2A
python smoke_foodtec.py
```

**Note**: Use the `canonical_price` returned from validation in the acceptance call.

## Testing Options

### Option 1: Automated Test Suite (Recommended)
Run the complete test suite that automatically starts server, tests all endpoints, and shows detailed request/response data:
```powershell
cd tests
.\run_all.ps1
```

### Option 2: Manual Testing
Start the server manually and run individual commands to see exactly what's happening:
```powershell
# Terminal 1: Start server
cd proxy
python main.py

# Terminal 2: Run manual tests (see commands above)
```
