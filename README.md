# Orcha-1# Orcha-1# Orcha-1: FoodTec Integration System# Orcha-1



Restaurant ordering system: MCP → Proxy → FoodTec API



## SetupMCP → Proxy → API



### 1. Install Dependencies



```bash## Quick Start## OverviewMCP → Proxy → API

# MCP Server

cd MCP

npm install

npm run build### 1. Install Dependencies



# P2A (Python API Client)

cd P2A

pip install -r requirements.txt```bashA Model Context Protocol (MCP) based system for integrating with FoodTec's ordering API. The architecture follows a three-layer design:## Install



# Proxy Server# MCP Server

cd proxy

pip install -r requirements.txtcd MCP```



# UI (optional)npm install

cd MCP/ui

npm installnpm run build```cd MCP && npm install && npm run build

```



### 2. Configure Environment

# Python Services (P2A + Proxy)UI (Express/TypeScript) → MCP Server (TypeScript) → Proxy (FastAPI/Python) → P2A (Python) → FoodTec APIcd P2A && pip install -r requirements.txt  

```bash

# Copy template and add FoodTec credentialscd ../P2A

cp P2A/.env.template P2A/.env

# Edit P2A/.env with your API credentialspip install -r requirements.txt```cd proxy && pip install -r requirements.txt

```



### 3. Start Servers

cd ../proxy```

Open 3 terminals:

pip install -r requirements.txt

```bash

# Terminal 1: Proxy (port 8080)## Architecture

cd proxy

python main.py# UI



# Terminal 2: MCP (port 9090)cd ../MCP/ui## Start Servers

cd MCP

node dist/index.jsnpm install



# Terminal 3: UI (port 3001)```### Components```

cd MCP/ui

npx ts-node --esm server.ts

```

### 2. Configure Environmentcd proxy && python main.py

### 4. Test



Open http://localhost:3001

- Export Menu → Validate Order → Accept OrderCopy `.env.template` to `.env` and add your FoodTec credentials.1. **UI Layer** (`MCP/ui/`)```



## Structure



```### 3. Start Servers   - Express server serving web interface```

MCP/          # TypeScript MCP server (port 9090)

proxy/        # FastAPI proxy (port 8080)

P2A/          # Python FoodTec client

automation/   # LLM workflows (optional)**Terminal 1 - Proxy:**   - Interactive menu browsing and order placementcd MCP && node dist/index.js

```

```bash

cd proxy   - Real-time validation and acceptance flow```

python main.py

# Runs on http://localhost:8080

```

2. **MCP Server** (`MCP/`)## UI Interface (MCPUI)

**Terminal 2 - MCP:**

```bash   - JSON-RPC endpoint for tool invocation

cd MCP

node dist/index.js   - Three main tools:The project includes a web-based UI for interacting with the MCP server.

# Runs on http://localhost:9090

```     - `foodtec.export_menu` - Retrieve menu data



**Terminal 3 - UI:**     - `foodtec.validate_order` - Validate order and get final price### Install & Run UI

```bash

cd MCP/ui     - `foodtec.accept_order` - Submit order to FoodTec```

npx ts-node --esm server.ts

# Runs on http://localhost:3001cd MCP/ui && npm install

```

3. **Proxy Layer** (`proxy/`)cd MCP/ui && npx ts-node --esm server.ts

## Test the System

   - FastAPI server routing MCP requests```

1. Open http://localhost:3001

2. Click **Export Menu** → Loads FoodTec menu (38 categories)   - Handles vendor-specific translation

3. Select category → item → size

4. Click **Validate Order** → Returns price with tax   - Price validation and invariant enforcementThe UI will be available at http://localhost:3001

5. Click **Accept Order** → Submits to FoodTec ✅



## Architecture

4. **P2A Layer** (`P2A/`)**Note:** The UI may crash when requesting menu export from MCP due to lack of caching at this stage. This will be addressed in a future update.

```

UI (3001) → MCP Server (9090) → Proxy (8080) → P2A → FoodTec API   - Python client for FoodTec API

```

   - Menu and order service abstractions### Features

- **UI**: Web interface for menu browsing and ordering

- **MCP**: JSON-RPC server exposing FoodTec tools   - API v1 and v2 format handling- View and export menu data

- **Proxy**: FastAPI server handling vendor translation

- **P2A**: Python client for FoodTec API- Validate orders



## Documentation## Getting Started- Accept orders



See `docs/` folder for:

- `ACCEPTANCE_FIX.md` - Price handling details

- `VENDOR_AGNOSTIC_API.md` - Future architecture### Prerequisites## Automation Component

- `HARDENING_CHECKLIST.md` - Security checklist



## Testing

- Python 3.11+The project includes an LLM-powered automation component for processing natural language orders.

```bash

# Run regression test- Node.js 18+

powershell -ExecutionPolicy Bypass -File .\scripts\test-accept.ps1

```- FoodTec API credentials### Install & Run Automation



## Project Structure```



```### Installationcd automation && npm install

orcha-1/

├── MCP/                 # MCP Server & UIcd automation && cp .env.example .env

│   ├── src/            # TypeScript source

│   ├── ui/             # Web UI1. **Clone and setup Python environment:**# Add your OpenAI API key to the .env file

│   └── MCP_tests/      # Tests

├── proxy/              # FastAPI proxy```bash```

├── P2A/                # FoodTec client

├── automation/         # LLM automation (optional)cd proxy

├── scripts/            # Test scripts

└── docs/               # Documentationpython -m venv .venv### Features

```

.venv\Scripts\activate  # Windows- Natural language order processing

## License

pip install -r requirements.txt- Integration with UI

Internal use only.

```- LLM-powered order extraction

- Automated order workflow

2. **Setup P2A dependencies:**

```bashSee `automation/README.md` for more details.

cd P2A

pip install -r requirements.txt## Test Entire Loop

``````

cd tests && .\run_all.ps1

3. **Setup MCP server:**
```bash
cd MCP
npm install
npm run build
```

4. **Setup UI:**
```bash
cd MCP/ui
npm install
```

5. **Configure environment:**
```bash
# Copy .env.template to .env and fill in FoodTec credentials
cp .env.template .env
```

### Running the System

**Terminal 1 - Proxy Server:**
```bash
cd proxy
python main.py
# Runs on http://localhost:8080
```

**Terminal 2 - MCP Server:**
```bash
cd MCP
node dist/index.js
# Runs on http://localhost:9090
```

**Terminal 3 - UI Server:**
```bash
cd MCP/ui
npx ts-node --esm server.ts
# Runs on http://localhost:3001
```

**Access the UI:**
Open http://localhost:3001 in your browser

## Usage Flow

1. **Export Menu** - Click to load FoodTec menu (38 categories)
2. **Select Item** - Browse categories, choose item and size
3. **Validate Order** - Validates with FoodTec, returns final price with tax
4. **Accept Order** - Submits order to FoodTec, returns order confirmation

## Key Concepts

### Price Handling

The system handles two price types:
- **Menu Price** (`menuPrice`): Item price without tax (e.g., $6.99)
- **Canonical Price** (`canonicalPrice`): Final price with tax (e.g., $7.41)

**Critical:** Accept always uses prices from validation - never re-validates to avoid tax-on-tax issues.

### Invariants Enforced

1. `canonicalPrice >= menuPrice` (tax included)
2. Phone format: `XXX-XXX-XXXX`
3. No re-validation on accept
4. Idempotency via `externalRef` and `idem` fields

## Testing

### Run Regression Test
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-accept.ps1
```

Expected output:
```
=== Testing Order Acceptance Flow ===
[1/3] Validating order...
Validation successful: canonicalPrice = 7.41
[2/3] Accepting order...
Acceptance successful with canonicalPrice=7.41
[3/3] Verifying order data...
=== All Tests Passed ===
```

### Run Invariant Tests
```bash
cd MCP/MCP_tests
npm install --save-dev @types/node  # First time only
npx ts-node test-accept-invariants.ts
```

## Project Structure

```
orcha-1/
├── MCP/                      # MCP Server & UI
│   ├── src/                  # TypeScript source
│   │   ├── tools/            # MCP tool definitions
│   │   ├── proxy/            # Proxy client
│   │   └── index.ts          # Main server
│   ├── ui/                   # Web UI
│   │   ├── public/           # Frontend (app.js, styles)
│   │   ├── views/            # Handlebars templates
│   │   └── server.ts         # Express server
│   └── MCP_tests/            # Test files
├── proxy/                    # FastAPI proxy server
│   ├── handlers.py           # JSON-RPC handlers
│   └── main.py               # FastAPI app
├── P2A/                      # FoodTec API client
│   ├── core/                 # Service layer
│   │   ├── menu_service.py
│   │   ├── order_service.py
│   │   └── api_client.py
│   └── models/               # Data models
├── scripts/                  # Test scripts
│   └── test-accept.ps1       # Regression test
└── docs/                     # Documentation
    ├── ACCEPTANCE_FIX.md     # Price handling fix
    ├── VENDOR_AGNOSTIC_API.md # Future architecture
    ├── HARDENING_CHECKLIST.md # Implementation tracking
    └── STEP_BY_STEP_SUMMARY.md # Complete summary
```

## Documentation

- **[ACCEPTANCE_FIX.md](docs/ACCEPTANCE_FIX.md)** - Detailed explanation of the menuPrice/canonicalPrice fix
- **[VENDOR_AGNOSTIC_API.md](docs/VENDOR_AGNOSTIC_API.md)** - Planned vendor-agnostic refactor
- **[HARDENING_CHECKLIST.md](docs/HARDENING_CHECKLIST.md)** - Security and robustness checklist
- **[STEP_BY_STEP_SUMMARY.md](docs/STEP_BY_STEP_SUMMARY.md)** - Complete implementation summary

## Known Limitations

### Vendor Coupling
Currently, the system is tightly coupled to FoodTec:
- Tool names include `foodtec.*` prefix
- "Canonical price" is FoodTec terminology
- Two-step validate→accept flow is FoodTec-specific

**Future:** See `docs/VENDOR_AGNOSTIC_API.md` for planned refactor to support multiple vendors (Toast, Square, etc.)

## Troubleshooting

### Accept Order Fails
- Ensure validation was run first
- Check phone format is `XXX-XXX-XXXX`
- Verify item name matches menu exactly

### Menu Not Loading
- Check proxy server is running on port 8080
- Verify FoodTec credentials in `.env`
- Check network connectivity

### Price Mismatch Errors
- Never modify prices after validation
- Always send both `menuPrice` and `canonicalPrice` to accept
- If prices change, re-validate before accepting

## Contributing

When making changes:
1. Run regression tests
2. Update documentation
3. Ensure all services start without errors
4. Test full UI flow (Export → Validate → Accept)

## License

Internal use only.

---

**Last Updated:** October 2, 2025  
**Status:** Production Ready  
**Version:** 1.0.0
