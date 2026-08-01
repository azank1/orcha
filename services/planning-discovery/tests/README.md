# Planning & Discovery Service — Test Suite

## Overview

Comprehensive test suite for the Planning & Discovery service covering:
- **Unit tests** (70): Fast, deterministic, mocked dependencies
- **Integration tests** (20): Database operations, vector indices, manifest processing
- **Coverage target**: >70%

## Test Structure

```
tests/
├── conftest.py                          # Shared fixtures & configuration
├── unit/
│   ├── test_template_generator.py       # TDWA semantic templates
│   ├── test_dag_validator.py            # DAG validation logic
│   ├── test_keyword_extraction.py       # Query keyword extraction
│   ├── test_deterministic_validator.py  # Deterministic DAG validation
│   └── __init__.py
├── integration/
│   ├── test_manifest_processing.py      # Manifest → embedding flow
│   ├── test_db_operations.py            # Database CRUD operations
│   ├── test_vector_indices.py           # Vector index setup & queries
│   └── __init__.py
└── README.md
```

## Running Tests

### All Tests
```bash
make pnd-test
```

### Unit Tests Only (Fast)
```bash
make pnd-test-unit
# or: uv run pytest services/planning-discovery/tests/ -m unit
```

### Integration Tests
```bash
uv run pytest services/planning-discovery/tests/ -m integration
```

### With Coverage Report
```bash
make pnd-test-cov
# Report: htmlcov/index.html
```

### Specific Test File
```bash
uv run pytest services/planning-discovery/tests/unit/test_template_generator.py -v
```

### Watch Mode (requires pytest-watch)
```bash
uv run ptw services/planning-discovery/tests/
```

## Test Configuration

### Environment
- **Test DB**: Same as dev (`DATABASE_URL`)
- **LLM**: Ollama (local, no API key)
- **Kafka**: Local broker on port 9092

See [.env.test](.env.test) for test configuration.

### Markers
```bash
# Run only marked tests
uv run pytest -m unit              # Unit tests
uv run pytest -m integration       # Integration tests
uv run pytest -m db                # Database tests
uv run pytest -m "not slow"        # Exclude slow tests (>1s)
```

## Test Coverage

### Unit Tests

#### Manifest Processing
- **test_template_generator.py**: TDWA semantic string generation
  - Minimal and full manifests
  - Capability formatting
  - Network extraction
  - Reliability calculation

#### Planning & Decomposition
- **test_dag_validator.py**: DAG validation
  - Linear task chains
  - Parallel branches
  - Circular dependency detection
  - Invalid reference detection

#### Resolution
- **test_keyword_extraction.py**: Query keyword extraction
  - Simple/complex query handling
  - Special character handling
  - Deduplication

#### Validation
- **test_deterministic_validator.py**: DAG validation logic
  - Simple DAGs
  - DAGs with dependencies
  - Invalid variable references
  - Router nodes

### Integration Tests

#### Manifest Processing
- **test_manifest_processing.py**: Template → embedding pipeline
  - Multi-manifest processing
  - LLM integration with mocks

#### Database Operations
- **test_db_operations.py**: Database connectivity
  - Agent insertion/retrieval
  - Full-text search vectors
  - Tag-based filtering
  - Protocol filtering

#### Vector Operations
- **test_vector_indices.py**: Vector index setup
  - Extension availability (pgvector, pg_trgm)
  - Index existence verification
  - Generated columns
  - Vector similarity queries

## Prerequisites

### Required for Running Tests
1. **PostgreSQL** with vector extension
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql-15-pgvector

   # macOS
   brew install pgvector
   ```

2. **Ollama** (for E2E tests, optional)
   ```bash
   # Download: https://ollama.ai
   ollama pull llama2
   ollama pull nomic-embed-text
   ```

3. **Kafka** (for manifest consumer tests, optional)
   ```bash
   make kafka-up
   make kafka-topics
   ```

### Database Setup

1. **Create test database**
   ```bash
   createdb orcha_dev  # Use dev database for tests
   ```

2. **Run migrations**
   ```bash
   make migrate
   ```

3. **Create vector indices**
   ```bash
   make pnd-db-init
   ```

## Key Fixtures

### Configuration
- **event_loop**: Async event loop for tests
- **test_db_pool**: asyncpg connection pool
- **clean_db**: Auto-cleanup of database tables

### Agent Manifests
- **minimal_agent_manifest**: Simple test agent
- **crypto_oracle_manifest**: Full manifest with capabilities
- **payment_agent_manifest**: Multi-network agent

### Database Seeding
- **seed_agents**: Inserts test agents
- **seed_embeddings**: Inserts agent embeddings
- **db_conn**: Single connection for queries

### Mocks
- **mock_llm_provider**: Mocked LLM with deterministic responses
- **mock_db_pool**: Mocked asyncpg pool
- **mock_kafka_producer/consumer**: Mocked Kafka components

## Debugging Tests

### Verbose Output
```bash
uv run pytest services/planning-discovery/tests/ -vv
```

### Show Print Statements
```bash
uv run pytest services/planning-discovery/tests/ -s
```

### Stop on First Failure
```bash
uv run pytest services/planning-discovery/tests/ -x
```

### Run Last Failed Tests
```bash
uv run pytest services/planning-discovery/tests/ --lf
```

### Debug Mode
```bash
uv run pytest services/planning-discovery/tests/ --pdb
```

## Performance Notes

- Unit tests: <100ms each
- Integration tests: 100ms-1s (depending on DB)
- Full suite: ~10-15s on modern hardware

For CI/CD, consider:
- Running unit tests in parallel: `pytest -n auto`
- Skipping integration tests in fast mode: `pytest -m unit`

## Common Issues

### Vector Extension Not Found
```
ProgrammingError: type "vector" does not exist
```
**Solution**: Install pgvector extension and run `make pnd-db-init`

### Ollama Connection Failed
```
Failed to connect to Ollama at http://localhost:11434
```
**Solution**: Start Ollama (`ollama serve`) or skip E2E tests

### Database Already in Use
```
ERROR: database "orcha_test" is being accessed by other users
```
**Solution**: Close other connections or use different test database

## Contributing

When adding tests:
1. Follow existing naming convention: `test_<feature>.py`
2. Use appropriate marker: `@pytest.mark.unit` or `@pytest.mark.integration`
3. Document what the test validates in docstring
4. Use fixtures from `conftest.py` for common setup
5. Aim for >80% coverage in modified modules

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Commits to main/develop
- Manual trigger

Run locally before pushing:
```bash
make pnd-test  # Planning-Discovery tests
make test      # Registry tests
make ci        # All checks (lint, format, test)
```

# Test Query for testing the /plan api

Plan a 7-day trip from London to Tokyo next month — find available flights from LHR to NRT, book a hotel near Shibuya for 5 nights within a budget of £150 per night, check the weather forecast for the travel dates, convert my £2000 spending budget to JPY, and create a day-by-day itinerary focused on food and culture.
