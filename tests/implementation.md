# Tests Implementation - Unified Test Suite

Root-level test suite covering both P2A direct integration and proxy JSON-RPC wrapper.

## Architecture

```
tests/
├── test_smoke_p2a.py      # Direct P2A → FoodTec API test
├── test_smoke_proxy.py    # JSON-RPC → Proxy → P2A → FoodTec test  
├── fixtures/
│   └── payload_fixture.json  # Canonical test payloads
├── run_all.ps1           # Windows test runner
└── run_all.sh            # Linux/macOS test runner
```

## Test Strategy

### Direct Integration Test
- **File**: `test_smoke_p2a.py`
- **Purpose**: Validate P2A package directly against FoodTec API
- **Flow**: Menu export → Validation → Acceptance
- **No dependencies**: Direct API calls, no server required

### Proxy Integration Test  
- **File**: `test_smoke_proxy.py`
- **Purpose**: Validate complete JSON-RPC proxy integration
- **Flow**: JSON-RPC client → Proxy server → P2A → FoodTec API
- **Requires**: Proxy server running on port 8080

### Fixture-Based Testing
- **Single source of truth**: `fixtures/payload_fixture.json`
- **Canonical payloads**: Aligned with Universal Truth specification  
- **Prevents drift**: All tests use same payload structure

## Test Runners

### Automated Suite
```bash
# Windows
.\run_all.ps1

# Linux/macOS  
./run_all.sh
```

**Automated Process:**
1. Run P2A direct test
2. Start proxy server in background
3. Run proxy JSON-RPC test
4. Stop proxy server
5. Report results

### Manual Testing
```bash
# P2A direct only
python test_smoke_p2a.py

# Proxy only (requires server running)
python test_smoke_proxy.py
```

## Expected Results

### P2A Direct Test
```
[1] Testing Menu Export...
   PASS: Status 200, 38 categories
   Selected: 3pcs Chicken Strips w/ FF (Lg) - $6.99

[2] Testing Order Validation...  
   PASS: Status 200, canonical price: $7.41

[3] Testing Order Acceptance...
   PASS: Status 200, Order ID: 15

P2A Direct API test passed!
```

### Proxy JSON-RPC Test
```
[1] Testing Menu Export...
   PASS: Menu export successful: 38 categories

[2] Testing Order Validation...
   PASS: Validation successful: canonical price $7.41

[3] Testing Order Acceptance...
   PASS: Acceptance successful: Order ID 16

Proxy JSON-RPC test passed!
```