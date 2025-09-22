# Testing Scripts

This directory contains PowerShell scripts for testing various components of the Orcha project.

## MCP Test Scripts

Simple PowerShell scripts to test the MCP server functionality.

### Quick Start

1. Start the MCP Server
```powershell
.\scripts\run-mcp.ps1
```

2. Run All MCP Tests (in a separate terminal)
```powershell
.\scripts\test-all.ps1
```

### Individual MCP Tests

- `.\scripts\test-health.ps1` - Test health endpoint
- `.\scripts\test-discovery.ps1` - Test tool discovery
- `.\scripts\test-validation-error.ps1` - Test validation errors
- `.\scripts\test-valid-request.ps1` - Test valid requests

### MCP Success Criteria

✅ Health check returns `{ ok: true }`  
✅ Discovery shows exactly 3 tools  
✅ Wrong params produce JSON-RPC error with `-32602`  
✅ Valid request produces schema-shaped response  

### Example Request

See `docs/examples/menu.export.req.json` for a valid request example.

## Proxy Test Scripts

Test scripts for the enhanced proxy server with idempotency, logging, and health checks.

### Quick Start

1. Start the Proxy Server
```
cd proxy && npm start
```

2. Run All Proxy Tests
```powershell
.\scripts\run-proxy-tests.ps1
```

### Individual Proxy Tests

- `.\scripts\test-proxy-health.ps1` - Test proxy health endpoint
- `.\scripts\test-proxy-idempotency.ps1` - Test idempotency handling for orders
- `.\scripts\test-proxy-logging.ps1` - Test structured logging capabilities

### Proxy Success Criteria

✅ Health endpoint returns structured status with `ok: true`  
✅ Idempotent requests return identical responses with replay headers  
✅ Missing idempotency key is properly rejected  
✅ Request IDs are tracked correctly through the request lifecycle  
✅ Structured JSON logs include all required metadata  

## Requirements

- Windows PowerShell 5.1 or later
- For MCP tests: MCP server running on default port
- For Proxy tests: Proxy server running on http://localhost:8080