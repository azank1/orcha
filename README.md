# Orcha-1

MCP → Proxy → API

## Install
```
cd MCP && npm install && npm run build
cd P2A && pip install -r requirements.txt  
cd proxy && pip install -r requirements.txt
```

## Start Servers
```
cd proxy && python main.py
```
```
cd MCP && node dist/index.js
```

## UI Interface (MCPUI)

The project includes a web-based UI for interacting with the MCP server.

### Install & Run UI
```
cd MCP/ui && npm install
cd MCP/ui && npx ts-node server.ts
```

The UI will be available at http://localhost:3001

**Note:** The UI may crash when requesting menu export from MCP due to lack of caching at this stage. This will be addressed in a future update.

### Features
- View and export menu data
- Validate orders
- Accept orders

## Test Entire Loop
```
cd tests && .\run_all.ps1
