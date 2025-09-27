# Proxy Implementation - JSON-RPC Server

FastAPI server that wraps P2A package with JSON-RPC 2.0 protocol.

## Architecture

```
proxy/
├── main.py          # FastAPI application entry point  
├── handlers.py      # JSON-RPC method dispatcher
├── requirements.txt # FastAPI dependencies
└── smoke_proxy.py   # Local development test
```

## Stack
- **Server**: FastAPI with uvicorn
- **Protocol**: JSON-RPC 2.0 over HTTP
- **Integration**: Direct import of P2A services
- **Async**: run_in_threadpool for P2A sync calls

## Endpoints

### Health Check
```
GET /healthz → {"ok": true, "service": "Proxy"}
```

### JSON-RPC Methods
```
POST /rpc
- foodtec.export_menu
- foodtec.validate_order  
- foodtec.accept_order
```

## Test Suite

### Local Development Test
```bash
# Terminal 1: Start server
python main.py

# Terminal 2: Test endpoints  
python smoke_proxy.py
```

### Integration Test
```bash
# From root directory (requires server running)
python tests\test_smoke_proxy.py
```

## Key Implementation Details

### JSON-RPC Request Format
```json
{
  "jsonrpc": "2.0",
  "id": "unique-id",
  "method": "foodtec.export_menu",
  "params": { "order_type": "D" }
}
```

### Error Handling
- Proper JSON-RPC 2.0 error responses
- Exception handling with debug information
- HTTP 200 for both success and JSON-RPC errors

### P2A Integration
- Direct import: `from P2A.core.menu_service import MenuService`
- Parameter mapping between JSON-RPC and P2A service methods
- Async wrapper around sync P2A calls using FastAPI's run_in_threadpool