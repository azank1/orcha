# P2A Implementation - FoodTec API Integration

Direct HTTP client package for FoodTec API integration.

## Architecture

```
P2A/
├── core/
│   ├── api_client.py       # HTTP client with auth
│   ├── menu_service.py     # Menu export logic
│   └── order_service.py    # Validation/acceptance logic
├── models/                 # Data models
├── smoke_foodtec.py       # Direct API test
└── requirements.txt       # Dependencies
```

## Stack
- **HTTP Client**: httpx with BasicAuth
- **Environment**: python-dotenv for credentials
- **Models**: Pydantic for data validation

## Test Suite

### Direct API Test
```bash
python smoke_foodtec.py
```

**Expected Flow:**
1. Menu Export: GET /menu/categories → 38 categories
2. Order Validation: POST /validate/order → canonical price $7.41  
3. Order Acceptance: POST /orders → Order ID created

### Integration Test
```bash
# From root directory
python tests\test_smoke_p2a.py
```

## Key Implementation Details

### Price Flow
- **Menu Price**: Original item price (e.g., $6.99)
- **Validation**: Uses original price → Returns canonical price (e.g., $7.41)
- **Acceptance**: Uses canonical price from validation

### Required Payload Structure
- **Phone Format**: "410-555-1234" (with area code and hyphens)
- **Source**: Must be "Voice" 
- **Category**: Required for validation (e.g., "Appetizer")
- **External Ref**: Consistent across validate/accept calls

### Authentication
- Separate credentials for each endpoint (menu, validate, accept)
- BasicAuth headers with environment-based credentials
- Automatic retry logic for connection issues
menu_service = MenuService(client)
order_service = OrderService(client)

# Menu
menu_result = menu_service.export_menu("Pickup")
item = menu_service.pick_first_item(menu_result["data"])

# Validate -> Accept flow
validation_result = order_service.validate_order(item)
canonical_price = validation_result["canonical_price"]

acceptance_result = order_service.accept_order(
    validation_result["payload"], 
    canonical_price
)
```

### Environment Setup
```bash
# Copy template and fill credentials
cp .env.template .env

# Install minimal dependencies
pip install -r requirements.txt

# Run smoke test
python smoke_test.py
```

## Key Requirements (Locked from Documentation)
- **Source**: Must be "Voice" (only supported value)
- **Phone Format**: "410-848-1234" (with area code)
- **Category**: Required in validation payload
- **Price**: Use validation's canonical price in acceptance
- **External Ref**: Consistent across validate/accept calls
- **Size Token**: Exact match from menu (e.g., "Lg" not "Regular")

## Success Criteria
✅ Menu Export: 200 OK, 38 categories  
✅ Order Validation: 200 OK, canonical price returned  
✅ Order Acceptance: 200 OK, using validation's canonical price

## Dependencies
- `httpx==0.27.0` - HTTP client
- `python-dotenv==1.0.1` - Environment variables

**Total: 2 dependencies, ~125 lines of code, 100% working E2E flow**