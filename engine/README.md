# Engine: MCP Server + Proxy Setup

## Current Stage (Stage 1: Scaffold + Cleanup)
We now have a clean repo with **two main services**:

1. **Proxy (`/proxy`)**
   - Express server running on **port 8080**
   - Acts as the upstream **API client proxy**
   - Features:
     - Structured JSON logging with request tracking
     - Proper idempotency handling for order acceptance
     - Request ID tracking across the request lifecycle
     - Enhanced health endpoint with service metadata
   - Endpoints:
     - `/apiclient/acceptOrder` - Submit new orders (requires Idempotency-Key)
     - `/healthz` - Service health status

2. **MCP Server (`/mcp_server`)**
   - MCP-style **JSON-RPC server** running on **port 9090**
   - Wraps the proxy and exposes structured MCP tools
   - Tools currently exposed:
     - `foodtec.export_menu` → proxy `/menu`
     - `foodtec.validate_order` → proxy `/validateOrder`
     - `foodtec.accept_order` → proxy `/acceptOrder`
   - Health endpoint → `/healthz`
   - Tool discovery endpoint → `/.well-known/mcp/tools`

## Implementation Roadmap

### Stage 1: Scaffold + Cleanup ✓
- [x] 1.1 Clean the repo, document the architecture
- [x] 1.2 Document OpenAPI spec in `/openapi`
- [x] 1.3 Enhance proxy with proper idempotency, logging, and health checks
  - [x] Implement strict idempotency key requirement for order acceptance
  - [x] Add response caching with replay detection
  - [x] Implement structured JSON logging with request IDs
  - [x] Create enhanced health endpoint
  - [x] Add comprehensive test scripts

### Stage 2: API Enhancements (In Progress)
- [ ] 2.1 Add order status endpoint with simulated state machine
- [ ] 2.2 Add order update/cancel functionality
- [ ] 2.3 Add validation improvements and error simulation

### Stage 3: MCP Improvements
- [ ] 3.1 Improve MCP schemas with OpenAPI alignment
- [ ] 3.2 Add new MCP tools for order status and updates
- [ ] 3.3 Add streaming events option for order status

---

## Running Locally

Clone repo:
```bash
git clone https://github.com/<org-or-user>/engine.git
cd engine

##Proxy run 

cd proxy
npm install
npm run build
npm start


##mcp run

cd ../mcp_server
npm install
npm run build
npm start
```

## Testing

### Proxy Tests

```powershell
# Run all proxy tests
.\scripts\run-proxy-tests.ps1

# Or run individual test scripts
.\scripts\test-proxy-health.ps1
.\scripts\test-proxy-idempotency.ps1
.\scripts\test-proxy-logging.ps1
```

### MCP Tests

```powershell
# Run all MCP tests
.\scripts\test-all.ps1
