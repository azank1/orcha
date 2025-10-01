# FoodTec Integration Repository Structure

Complete file structure following clean architecture principles with clear separation of concerns.

## Repository Tree

```
orcha-1/
├── .env                      # Root environment (shared)
├── .gitignore                # Ignore venv, local docs, etc.
├── README.md                 # High-level repo doc
├── COMPLETE_STRUCTURE.md     # Full repo tree snapshot
├── STRUCTURE.md              # Architecture overview (this file)
│
├── tests/                    # Root-level test runner (all directories feed here)
│   ├── test_smoke_p2a.py     # Direct FoodTec API test
│   ├── test_smoke_proxy.py   # Proxy loop test (RPC)
│   ├── fixtures/             # Canonical payloads
│   │   └── payload_fixture.json
│   └── run_all.sh            # One-command test runner (Linux/macOS)
│       run_all.ps1           # One-command test runner (Windows/PowerShell)
│
├── P2A/                      # Vendor adapter package
│   ├── __init__.py
│   ├── README.md
│   ├── requirements.txt
│   ├── smoke_foodtec.py      # Direct standalone tester (dev use only)
│   ├── core/
│   │   ├── api_client.py     # HTTPX + BasicAuth + retries
│   │   ├── menu_service.py   # Menu export service
│   │   └── order_service.py  # Validation + acceptance
│   └── models/
│       ├── menu.py           # Menu models
│       └── order.py          # Order/validation/acceptance models
│
├── proxy/                    # JSON-RPC Proxy
│   ├── __init__.py
│   ├── main.py               # FastAPI app (entrypoint)
│   ├── handlers.py           # Handle RPC requests → P2A
│   ├── requirements.txt
│   ├── README.md
│   └── smoke_proxy.py        # Local dev test hitting /rpc
│
└── docs/                     # Gitignored local docs
    ├── foodtec_universal.md  # Canonical spec (Universal Truth)
    ├── payload_translation.md
    └── lessons_learned.md
```

## Architecture Layers

### Layer 1: Direct API Integration (P2A)
- **Purpose**: Direct HTTP client for FoodTec API
- **Pattern**: Service layer with business logic
- **Testing**: Direct API calls, no dependencies
- **Location**: `P2A/`

### Layer 2: JSON-RPC Proxy (Proxy)
- **Purpose**: Wrapper around P2A with JSON-RPC protocol
- **Pattern**: FastAPI server importing P2A directly
- **Testing**: HTTP requests to proxy endpoints
- **Location**: `proxy/`

### Layer 3: Integration Testing (Tests)
- **Purpose**: End-to-end validation of both layers
- **Pattern**: Root-level test suite with fixtures
- **Testing**: Both direct and proxy flows
- **Location**: `tests/`

## Key Design Principles

### Separation of Concerns
- **P2A**: Pure FoodTec integration, no web server concerns
- **Proxy**: Pure JSON-RPC handling, delegates to P2A
- **Tests**: Pure testing, uses canonical fixtures

### Single Source of Truth
- **Payloads**: `tests/fixtures/payload_fixture.json`
- **API Spec**: `docs/foodtec_universal.md`
- **Business Logic**: `P2A/core/order_service.py`

### Fixture Discipline
- All tests import from `tests/fixtures/`
- No duplicate payload definitions
- Alignment validation enforced

## File Responsibilities

### Core Implementation
- `P2A/core/api_client.py`: HTTP requests, auth, retries
- `P2A/core/menu_service.py`: Menu processing
- `P2A/core/order_service.py`: Order validation/acceptance
- `proxy/handlers.py`: JSON-RPC method routing

### Configuration & Environment
- `.env`: FoodTec credentials (root level)
- `P2A/requirements.txt`: Direct API dependencies
- `proxy/requirements.txt`: FastAPI dependencies

### Testing & Validation
- `tests/test_smoke_p2a.py`: Direct API integration test
- `tests/test_smoke_proxy.py`: JSON-RPC proxy test
- `tests/fixtures/payload_fixture.json`: Canonical payloads
- `tests/run_all.*`: One-command test runners

### Documentation
- `docs/foodtec_universal.md`: Universal Truth specification
- Each component has README.md with usage examples

## Success Metrics

- ✅ **P2A Package**: Direct FoodTec API integration working
- ✅ **Proxy Server**: JSON-RPC wrapper functional
- ✅ **Test Suite**: Both layers validated end-to-end
- ✅ **Fixture Alignment**: Payloads synchronized across all tests
- ✅ **Documentation**: Clear specs and usage guides

This structure supports independent development of each layer while ensuring integration correctness through shared fixtures and comprehensive testing.