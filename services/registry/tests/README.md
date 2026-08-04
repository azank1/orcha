# Registry Service Tests

Comprehensive test suite for the Registry microservice.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── fixtures/                # Test data files
│   ├── mcp_emerge.yaml     # Valid MCP agent config
│   ├── a2a_emerge.yaml     # Valid A2A agent config
│   └── invalid_emerge.yaml # Invalid config for validation tests
├── test_validation.py       # Validation service tests
├── test_mcp_adapter.py      # MCP adapter tests
├── test_a2a_adapter.py      # A2A adapter tests
└── README.md               # This file
```

## Running Tests

### All Tests

```bash
# From monorepo root
make test

# Or with uv
uv run pytest services/registry/tests/
```

### With Coverage

```bash
make test-cov

# Or with uv
uv run pytest services/registry/tests/ \
  --cov=services/registry/src \
  --cov-report=html \
  --cov-report=term
```

### Specific Test Files

```bash
# Validation tests only
uv run pytest services/registry/tests/test_validation.py -v

# MCP adapter tests only
uv run pytest services/registry/tests/test_mcp_adapter.py -v

# A2A adapter tests only
uv run pytest services/registry/tests/test_a2a_adapter.py -v
```

### By Test Markers

```bash
# Unit tests only
uv run pytest -m unit

# Integration tests only
uv run pytest -m integration

# Adapter tests only
uv run pytest -m adapter
```

## Test Coverage

Current test coverage includes:

### ✅ Validation Service
- Valid MCP configuration parsing
- Valid A2A configuration parsing
- Invalid DID format detection
- Invalid protocol type detection
- Invalid transport type detection
- Missing required fields (endpoint, command)
- mTLS configuration validation
- Health endpoint URL validation
- Semantic versioning validation

### ✅ MCP Adapter
- Successful capability harvesting (tools, resources, prompts)
- Connection error handling
- Partial failure recovery
- Retry logic with exponential backoff
- Health check success/failure
- x402 payment metadata extraction (from metadata and headers)
- Parallel harvesting

### ✅ A2A Adapter
- Successful capability harvesting from Agent Card
- Pre-parsed Agent Card support
- Unsupported schema version handling
- Invalid skill handling
- Connection error handling
- Retry logic
- Health check
- Agent-level authentication (invariant check)
- Well-known endpoint fetching

## Test Fixtures

### MCP Fixture (`mcp_emerge.yaml`)
- Valid MCP agent configuration
- SSE transport
- x402 payment enabled
- API key authentication

### A2A Fixture (`a2a_emerge.yaml`)
- Valid A2A agent configuration
- HTTP transport
- OAuth2 authentication
- No payment

### Invalid Fixture (`invalid_emerge.yaml`)
- Multiple validation failures
- Used to test error handling

## Mocked Responses

Tests use mocked HTTP responses for:
- MCP `tools/list`, `resources/list`, `prompts/list` calls
- A2A Agent Card fetching
- Health check endpoints
- x402 payment headers

See `conftest.py` for fixture definitions.

## Writing New Tests

### 1. Add Test File

```python
# test_my_feature.py
import pytest
from services.registry.src.my_module import MyClass


class TestMyFeature:
    def test_something(self):
        # Test implementation
        assert True
```

### 2. Use Fixtures

```python
def test_with_database(db, test_user_id):
    # db and test_user_id are fixtures from conftest.py
    db.user.find_unique.return_value = Mock(id=test_user_id)
```

### 3. Mark Tests

```python
@pytest.mark.unit
def test_unit_logic():
    pass


@pytest.mark.integration
async def test_integration():
    pass


@pytest.mark.slow
def test_slow_operation():
    pass
```

## CI Integration

Tests run automatically in GitHub Actions on:
- Pull requests
- Pushes to main/develop branches

See `.github/workflows/ci.yml` for configuration.

## Test Database

For integration tests, use the test database:

```bash
# Set in environment
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/orcha_test"

# Run migrations
cd common/database
uv run prisma migrate deploy
```

## Debugging Tests

### Verbose Output

```bash
uv run pytest -vv
```

### Stop on First Failure

```bash
uv run pytest -x
```

### Run Specific Test

```bash
uv run pytest tests/test_validation.py::TestValidationService::test_validate_valid_mcp_config
```

### Print Output

```bash
uv run pytest -s  # Don't capture stdout
```

## Coverage Goals

- **Overall**: > 80%
- **Critical paths**: > 90%
- **Adapters**: > 85%
- **Validation**: > 95%

Run `make test-cov` to see current coverage.
