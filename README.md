# Orcha-1

Restaurant ordering system: MCP  Proxy  FoodTec API

## Setup

### 1. Install Dependencies

```bash
# MCP Server
cd MCP
npm install
npm run build

# P2A (Python API Client)
cd P2A
pip install -r requirements.txt

# Proxy Server
cd proxy
pip install -r requirements.txt

# UI (optional)
cd MCP/ui
npm install
```

### 2. Configure Environment

```bash
# Copy template and add FoodTec credentials
cp P2A/.env.template P2A/.env
# Edit P2A/.env with your API credentials
```

### 3. Start Servers

Open 3 terminals:

```bash
# Terminal 1: Proxy (port 8080)
cd proxy
python main.py

# Terminal 2: MCP (port 9090)
cd MCP
node dist/index.js

# Terminal 3: UI (port 3001)
cd MCP/ui
npx ts-node --esm server.ts
```

### 4. Test

Open http://localhost:3001
- Export Menu  Validate Order  Accept Order

## Structure

```
MCP/          # TypeScript MCP server (port 9090)
proxy/        # FastAPI proxy (port 8080)
P2A/          # Python FoodTec client
automation/   # LLM workflows (optional)
```