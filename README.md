## Orcha-1 - Restaurant Order Management System# FoodTec JSON-RPC Proxy Server



MCP server → Proxy → FoodTec API



## SetupRestaurant ordering system. MCP server → Proxy → FoodTec API.

```bash

cd MCP && npm install && npm run build && cd ..

cd P2A && pip install -r requirements.txt && cd ..  

cd proxy && pip install -r requirements.txt && cd ..## SetupRestaurant ordering system with MCP server, proxy, and API integration.

```

```bash

## Test

```bash# Install

cd tests && .\run_all.ps1

```cd MCP && npm install && npm run build && cd ..



## Runcd P2A && pip install -r requirements.txt && cd ..## SetupA complete end-to-end restaurant ordering system with Model Context Protocol (MCP) integration, featuring multi-layer architecture with comprehensive testing.Minimal JSON-RPC proxy server for FoodTec API integration.

```bash

# Terminal 1cd proxy && pip install -r requirements.txt && cd ..

cd proxy && python main.py



# Terminal 2  

cd MCP && node dist/index.js# Test everything

```

cd tests && .\run_all.ps1### Prerequisites

Ports: MCP=9090, Proxy=8080
```

- Node.js 18+

## Run

```bash- Python 3.8+## 🏗️ Architecture Overview## Quick Start

# Terminal 1: Proxy

cd proxy && python main.py- PowerShell



# Terminal 2: MCP Server  

cd MCP && node dist/index.js

```### Install Dependencies



## Ports```### 1. Setup Environment

- MCP: 9090

- Proxy: 8080```bash

# MCP ServerExternal Client → MCP Server → Proxy → P2A → FoodTec API```powershell

cd MCP

npm install    (JSON-RPC)      (9090)      (8080)   (Python)  (REST)# Copy environment template and add your FoodTec credentials

npm run build

cd ..```copy P2A\.env.template P2A\.env



# Python components# Edit P2A\.env with your credentials

cd P2A

pip install -r requirements.txt### Components```

cd ../proxy

pip install -r requirements.txt

cd ..

```- **MCP Server**: TypeScript ESM JSON-RPC server providing tool discovery and order management### 2. Install Dependencies



## Testing- **Proxy**: Python JSON-RPC bridge handling protocol translation```powershell



### Run All Tests- **P2A (Python-to-API)**: Adapter layer for FoodTec API integrationcd P2A

```powershell

cd tests- **FoodTec API**: External restaurant management systempip install -r requirements.txt

.\run_all.ps1

```cd ..\proxy  



### Individual Tests## 📁 Repository Structurepip install -r requirements.txt



#### Test P2A directlycd ..

```bash

cd tests``````

python test_smoke_p2a.py

```orcha-1/



#### Test Proxy├── README.md                 # This file - setup and testing guide### 3. Run Complete Test Suite (Automated)

```bash

cd proxy├── MCP/                      # Model Context Protocol server```powershell

python main.py &

cd ../tests  │   ├── src/                  # TypeScript source codecd tests

python test_smoke_proxy.py

```│   ├── dist/                 # Compiled JavaScript.\run_all.ps1



#### Test MCP Server│   ├── MCP_tests/            # MCP-specific tests```

```bash

cd MCP│   └── implementation.md     # Technical documentation**This script automatically:**

npm run build

node dist/index.js &├── proxy/                    # JSON-RPC proxy service- Starts the proxy server on port 8080

npx ts-node MCP_tests/test-all-tools.ts

```│   ├── *.py                  # Python proxy implementation- Tests all endpoints (health, menu export, validation, acceptance)



## Manual Testing│   └── proxy_tests/          # Proxy-specific tests- Shows request/response details for each test



### Start Services├── P2A/                      # Python-to-API adapter- Stops the server when done



```powershell│   ├── core/                 # Core adapters and services

# Start Proxy (Terminal 1)

cd proxy│   ├── models/               # Data models and schemas### 4. Start Server Manually (For Manual Testing)

python main.py

│   ├── P2A_tests/            # P2A-specific tests```powershell

# Start MCP Server (Terminal 2) 

cd MCP│   └── implementation.md     # Technical documentationcd proxy

npm run build

node dist/index.js├── tests/                    # Integration testspython main.py

```

│   ├── run_all.ps1          # Complete test suite runner# Server runs on http://127.0.0.1:8080

### Test Endpoints

│   ├── test_smoke_p2a.py    # P2A direct API tests```

#### Health Check

```powershell│   ├── test_smoke_proxy.py  # Proxy JSON-RPC tests

Invoke-WebRequest -Uri "http://127.0.0.1:9090/healthz"

```│   └── fixtures/            # Test data and fixtures## Manual API Testing



#### Menu Export└── docs/                    # Documentation and specifications

```json

POST http://127.0.0.1:9090/rpc```### Health Check

{

  "jsonrpc": "2.0",**PowerShell:**

  "id": "test-1",

  "method": "foodtec.export_menu",## 🚀 Quick Start```powershell

  "params": {

    "orderType": "Delivery"Invoke-WebRequest -Uri "http://127.0.0.1:8080/healthz" -Method GET

  }

}### Prerequisites```

```



#### Order Validation

```json- Node.js 18+ with TypeScript support### 1. Menu Export

POST http://127.0.0.1:9090/rpc

{- Python 3.8+**PowerShell:**

  "jsonrpc": "2.0", 

  "id": "test-2",- PowerShell (for Windows testing)```powershell

  "method": "foodtec.validate_order",

  "params": {$menuBody = '{"jsonrpc":"2.0","id":"menu-001","method":"foodtec.export_menu","params":{"order_type":"D"}}'

    "category": "Appetizer",

    "item": "3pcs Chicken Strips w/ FF",### SetupInvoke-WebRequest -Uri "http://127.0.0.1:8080/rpc" -Method POST -Body $menuBody -ContentType "application/json"

    "size": "Lg", 

    "price": 6.99,```

    "customer": {

      "name": "Test User",1. **Clone and navigate**:

      "phone": "410-555-1234"

    }   ```bash### 2. Order Validation

  }

}   git clone <repository>**PowerShell:**

```

   cd orcha-1```powershell

#### Order Acceptance  

```json   ```$validateBody = '{"jsonrpc":"2.0","id":"validate-001","method":"foodtec.validate_order","params":{"phone":"410-555-1234","category":"Appetizer","item_name":"3pcs Chicken Strips w/ FF","size_name":"Lg","original_price":6.99,"external_ref":"test-ref-123"}}'

POST http://127.0.0.1:9090/rpc

Headers: {"Idempotency-Key": "order-test-123"}Invoke-WebRequest -Uri "http://127.0.0.1:8080/rpc" -Method POST -Body $validateBody -ContentType "application/json"

{

  "jsonrpc": "2.0",2. **Install MCP dependencies**:```

  "id": "test-3", 

  "method": "foodtec.accept_order",   ```bash

  "params": {

    "category": "Appetizer",   cd MCP### 3. Order Acceptance

    "item": "3pcs Chicken Strips w/ FF",

    "size": "Lg",   npm install**PowerShell:**

    "price": 7.41,

    "customer": {   npm run build```powershell

      "name": "Test User", 

      "phone": "410-555-1234"   cd ..$acceptBody = '{"jsonrpc":"2.0","id":"accept-001","method":"foodtec.accept_order","params":{"phone":"410-555-1234","category":"Appetizer","item_name":"3pcs Chicken Strips w/ FF","size_name":"Lg","canonical_price":7.41,"external_ref":"test-ref-456"}}'

    }

  }   ```Invoke-WebRequest -Uri "http://127.0.0.1:8080/rpc" -Method POST -Body $acceptBody -ContentType "application/json"

}

``````



## Configuration3. **Install Python dependencies**:



- MCP Server: Port 9090   ```bash## Test Direct P2A (Bypass Proxy)

- Proxy Server: Port 8080

- Environment variables: See individual implementation.md files   cd P2A```powershell



## Troubleshooting   pip install -r requirements.txtcd P2A



### Common Issues   cd ../proxypython smoke_foodtec.py

- Port conflicts: Ensure ports 8080 and 9090 are available

- Module loading: Run `npm run build` after TypeScript changes   pip install -r requirements.txt  # if exists```

- Python dependencies: Install all requirements.txt files

- Test failures: Check that services are running before tests   cd ..



### Debug Mode   ```**Note**: Use the `canonical_price` returned from validation in the acceptance call.

```bash

# MCP with debug

DEBUG=* node dist/index.js

## 🧪 Testing## Testing Options

# Python with verbose logging

python main.py --verbose

```
### Complete End-to-End Test Suite### Option 1: Automated Test Suite (Recommended)

Run the complete test suite that automatically starts server, tests all endpoints, and shows detailed request/response data:

Run all tests across the entire system:```powershell

cd tests

```powershell.\run_all.ps1

cd tests```

.\run_all.ps1

```### Option 2: Manual Testing

Start the server manually and run individual commands to see exactly what's happening:

This executes:```powershell

1. **P2A Direct API Test** - Tests Python → FoodTec API# Terminal 1: Start server

2. **Proxy JSON-RPC Test** - Tests Proxy → P2A → FoodTec API  cd proxy

3. **MCP E2E Test** - Tests MCP → Proxy → P2A → FoodTec APIpython main.py



### Individual Component Testing# Terminal 2: Run manual tests (see commands above)

```

#### MCP Server Tests
```bash
cd MCP
npm run build
node dist/index.js &  # Start server
npx ts-node MCP_tests/test-all-tools.ts  # Run tests
```

#### Proxy Tests  
```bash
cd proxy
python main.py &  # Start proxy
cd ../tests
python test_smoke_proxy.py  # Run tests
```

#### P2A Direct Tests
```bash
cd tests
python test_smoke_p2a.py
```

## 🔧 Manual Testing

### 1. Start Services

Start all required services:

```powershell
# Terminal 1: Start P2A/Proxy
cd proxy
python main.py

# Terminal 2: Start MCP Server  
cd MCP
npm run build
node dist/index.js
```

### 2. Test Individual Endpoints

#### Health Checks
```powershell
# MCP Health
Invoke-WebRequest -Uri "http://127.0.0.1:9090/healthz"

# Tool Discovery
Invoke-WebRequest -Uri "http://127.0.0.1:9090/.well-known/mcp/tools"
```

#### Menu Export
```json
POST http://127.0.0.1:9090/rpc
{
  "jsonrpc": "2.0",
  "id": "test-1",
  "method": "foodtec.export_menu", 
  "params": {
    "orderType": "Delivery"
  }
}
```

#### Order Validation
```json
POST http://127.0.0.1:9090/rpc
{
  "jsonrpc": "2.0",
  "id": "test-2", 
  "method": "foodtec.validate_order",
  "params": {
    "category": "Appetizer",
    "item": "3pcs Chicken Strips w/ FF",
    "size": "Lg",
    "price": 6.99,
    "customer": {
      "name": "Test User",
      "phone": "410-555-1234"
    }
  }
}
```

#### Order Acceptance
```json
POST http://127.0.0.1:9090/rpc
Headers: {"Idempotency-Key": "order-test-123"}
{
  "jsonrpc": "2.0",
  "id": "test-3",
  "method": "foodtec.accept_order", 
  "params": {
    "category": "Appetizer",
    "item": "3pcs Chicken Strips w/ FF", 
    "size": "Lg",
    "price": 7.41,
    "customer": {
      "name": "Test User",
      "phone": "410-555-1234" 
    }
  }
}
```

## ✅ Expected Test Results

When running `.\run_all.ps1`, you should see:

```
Running All Tests
====================
[1] P2A Direct API Test...
   ✅ Status 200, 38 categories
   ✅ Status 200, canonical price: $7.41
   ✅ Status 200, Order ID: XX

[2] Starting Proxy Server...
[3] Proxy JSON-RPC Test...
   PASS: Menu export successful: 38 categories
   PASS: Validation successful: canonical price $7.41
   PASS: Acceptance successful: Order ID: XX

[4] Starting MCP Server...
[5] MCP E2E Test...
   ✅ Menu exported successfully!
   ✅ Order validated successfully
   ✅ Order accepted successfully
   ✅ MCP forwarding + payload format aligned

ALL TESTS PASSED
PASS: P2A Direct API working
PASS: Proxy JSON-RPC working  
PASS: MCP E2E integration working
PASS: End-to-end integration complete
```

## 🛠️ Development

### MCP Server Development
```bash
cd MCP
npm run dev  # Start in watch mode
```

### Adding New Tools
1. Update `src/tools.ts` with new tool definition
2. Add method handling in `src/rpc.ts`  
3. Add tests in `MCP_tests/`
4. Rebuild and test

### Configuration
- MCP Server: Port 9090 (configurable via `PORT` env var)
- Proxy Server: Port 8080 (configurable in proxy code)
- Environment variables: See individual implementation.md files

## 📚 Documentation

- [MCP Implementation Details](MCP/implementation.md)
- [P2A Implementation Details](P2A/implementation.md)
- [API Specifications](docs/)

## 🎯 Production Readiness

The system includes:
- ✅ Complete E2E testing coverage
- ✅ Error handling and validation
- ✅ Idempotency support for orders
- ✅ JSON-RPC protocol compliance
- ✅ TypeScript type safety
- ✅ Comprehensive logging
- ✅ Health check endpoints

Ready for production deployment with proper environment configuration.

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8080 and 9090 are available
2. **Module loading**: Run `npm run build` after TypeScript changes
3. **Python dependencies**: Install all requirements.txt files
4. **Test failures**: Check that all services are running before tests

### Debug Mode
Start services with debug logging:
```bash
# MCP with debug
DEBUG=* node dist/index.js

# Python with verbose logging  
python main.py --verbose
```
