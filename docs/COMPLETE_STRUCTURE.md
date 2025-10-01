# Complete Repository Structure

## Root Directory
```
orcha-1/
│
├── .env                     # Environment variables (FoodTec credentials)
├── .gitignore              # Git ignore rules
├── .venv/                  # Python virtual environment (excluded from git)
├── .vscode/                # VS Code workspace settings
│   └── settings.json
├── docs/                   # Documentation (local only, git ignored)
│   ├── do_not_make_simple_things_hard.md
│   ├── foodtec_e2e_flow.md
│   └── foodtec_translation_debug.md
├── README.md               # Repository documentation
├── STRUCTURE.md            # This file
└── p2a/                    # Main P2A implementation
    ├── .env.template       # Environment variables template
    ├── main.py             # CLI entry point
    ├── requirements.txt    # Python dependencies
    ├── core/               # Core implementation
    │   ├── __init__.py
    │   ├── api_clients/    # Direct API clients
    │   │   ├── __init__.py
    │   │   ├── accept_client.py
    │   │   ├── menu_client.py
    │   │   └── validate_client.py
    │   ├── services/       # Business logic layer
    │   │   ├── __init__.py
    │   │   ├── accept_service.py
    │   │   ├── menu_service.py
    │   │   └── validate_service.py
    │   └── utils/          # Shared utilities
    │       └── __init__.py
    ├── schemas/            # JSON schema references
    │   ├── menu_export.json
    │   ├── order_accept.json
    │   └── order_validate.json
    └── tests/              # Test suite
        ├── test_accept.py
        ├── test_all.py
        ├── test_menu.py
        └── test_validate.py
```

## File Counts
- **Total Files**: 27 Python files + 3 JSON schemas + 4 docs + 4 config files = 38 files
- **Code Files**: 27 Python files (excluding __pycache__)
- **Test Files**: 4 test files
- **API Clients**: 3 client files (menu, validate, accept)
- **Services**: 3 service files (orchestration layer)
- **Documentation**: 3 reference documents

## Working Endpoints
✅ **Menu Export**: `GET /menu/categories?orderType=Pickup`
- Status: 200 OK
- Categories: 38
- Client: `menu_client.py`
- Service: `menu_service.py`
- Test: `test_menu.py`

✅ **Order Validation**: `POST /validate/order`
- Status: 200 OK
- Canonical price: $7.41
- Client: `validate_client.py`
- Service: `validate_service.py`
- Test: `test_validate.py`

✅ **Order Acceptance**: `POST /orders`
- Status: 200 OK
- Using validation's canonical price
- Client: `accept_client.py`
- Service: `accept_service.py`
- Test: `test_accept.py`

## Dependencies
```
httpx==0.27.0        # HTTP client
python-dotenv==1.0.1 # Environment variables
```

## Key Design Principles
1. **Separation of Concerns**: API clients vs business logic vs tests
2. **Locked Requirements**: Following documented working patterns exactly
3. **No Over-Engineering**: Direct API calls, minimal abstraction
4. **Error Prevention**: Explicit handling of known failure patterns
5. **Testability**: Each endpoint individually testable + E2E flow

## Success Metrics
- All 3 endpoints return 200 OK
- E2E flow completes successfully
- Canonical price adoption working
- No scope creep or unnecessary complexity

This structure represents the final, minimal, working implementation of the FoodTec P2A integration following Informed Simplicity principles and locked to prevent future scope creep.