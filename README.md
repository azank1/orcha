# OrchaPOS - MVP Orcha-1




---### 1. Install Ollama (for LLM)



## 🚀 Quick Start```bash

# Download and install Ollama from https://ollama.com

### Prerequisites# Then pull the model:

- Python 3.11+ollama pull llama3.2

- Node.js 18+```

- Ollama desktop app with `gpt-oss:120b-cloud` model

- FoodTec API credentials (in `.env`)### 2. Install Dependencies



### 1. Install Dependencies```bash

# MCP Server

**Backend (Python):**cd MCP

```powershellnpm install

# Proxynpm run build

cd proxy

pip install -r requirements.txt# UI Server

cd MCP/ui

# Automation  npm install

cd ../automation

pip install -r requirements.txt# P2A (Python API Client)

cd P2A

# P2Apip install -r requirements.txt

cd ../P2A

pip install -r requirements.txt# Proxy Server

```cd proxy

pip install -r requirements.txt

**Frontend (TypeScript/Node):**```

```powershell

# MCP Server### 3. Configure Environment

cd ../MCP

npm install```bash

npm run build# Copy template and add FoodTec credentials

cp P2A/.env.template P2A/.env

# UI Server# Edit P2A/.env with your API credentials

cd ui```

npm install

npm run build### 4. Start Servers

```

Open 4 terminals:

# Terminal 3: MCP (port 9090)

### 3. Start All Servicescd MCP

node dist/index.js

**Terminal 1 - Proxy (Port 8080):**

```powershell# Terminal 4: UI (port 3001)

cd proxycd MCP/ui

python main.pynpx ts-node --esm server.ts

``````



**Terminal 2 - MCP Server (Port 9090):**### 5. Test

```powershell

cd MCPOpen http://localhost:3001

npm run dev

```**Manual Mode:**

- Export Menu → Select Item → Validate Order → Accept Order

**Terminal 3 - Automation API (Port 5000):**

```powershell**AI Mode:**

cd automation- Type: "I want 2 large chicken strips for pickup"

python api_server.py- Click "Process Order"

```- Watch the AI agent think and complete the order automatically



**Terminal 4 - UI Server (Port 3001):**## Structure

```powershell

cd MCP/ui```

node dist/server.jsMCP/          # TypeScript MCP server (port 9090)

```proxy/        # FastAPI proxy (port 8080)

P2A/          # Python FoodTec client

### 4. Open Browserautomation/   # LLM workflows (optional)

```
Navigate to: **http://localhost:3001**

---

## 🎯 Try These Queries

Paste these into the "Natural Language Order" input:

### Browse Menu
```
show me appetizers
```

### Check Price
```
How much is a large mozzarella sticks?
```

### Place Order
```
I want 3 piece chicken strips large for pickup, name John Smith phone 410-555-1234
```


## 📊 System Architecture

```
Browser (3001) 
  ↓ POST /api/automation/process-order
Automation API (5000) [Flask + Ollama LLM]
  ↓ JSON-RPC tool calls
MCP Server (9090) [TypeScript]
  ↓ HTTP /rpc
Proxy (8080) [FastAPI + P2A]
  ↓ REST API
FoodTec POS
```

## ✅ What Works

- ✅ Natural language understanding (Ollama LLM)
- ✅ Menu browsing ("show me appetizers")
- ✅ Price checking ("how much is X?")
- ✅ Full order placement (export → validate → accept)
- ✅ Real-time thinking bar (shows LLM reasoning)
- ✅ Order confirmation with celebration UI
- ✅ Tax calculation (menuPrice → canonicalPrice)
- ✅ Duplicate prevention (no repeated orders)
- ✅ Multi-turn agent loop (up to 5 iterations)

---

## 🐛 Troubleshooting

**Should see:** `gpt-oss:120b-cloud`

**If missing:**
```powershell
ollama pull gpt-oss:120b-cloud
```

### "Method not found" errors?

- Verify MCP server is running on port 9090
- Check proxy is running on port 8080
- Restart all services in order

---

## 🚧 Known Limitations

- Single item orders only
- No customizations (e.g., "no onions")
- Menu summary limited to 10 categories
- No order history tracking

---

## 📝 Tech Stack

- **LLM**: Ollama (gpt-oss:120b-cloud, 120B params)
- **Agent**: Multi-turn loop with context management
- **Backend**: Python (Flask, FastAPI), TypeScript (Node.js)
- **Frontend**: Vanilla JS + SSE streaming
- **Protocol**: MCP (Model Context Protocol) for tool calling
- **POS Integration**: FoodTec v1/v2 API

---


