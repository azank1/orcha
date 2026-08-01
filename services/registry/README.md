# Registry Microservice

The Registry microservice is the entry point for agent developers to register their AI agents into the Orcha ecosystem.

## Features

- **Agent Registration**: Accept registration requests via REST API
- **Protocol Adapters**: Support for MCP and A2A protocols
- **Capability Harvesting**: Automatic discovery of agent capabilities
- **Health Monitoring**: Background job to monitor agent health
- **Version Management**: Track changes across agent versions
- **gRPC API**: Internal APIs for Planning and Manifest Processing services

## Technology Stack

- **Python**: 3.12+
- **Framework**: FastAPI
- **ORM**: Prisma Client
- **Database**: PostgreSQL (Supabase)
- **gRPC**: grpcio
- **Scheduler**: APScheduler

## Setup

### Prerequisites

- Python 3.12+
- uv package manager
- PostgreSQL database (Supabase recommended)

### Installation

1. **Install dependencies** (from monorepo root):

```bash
uv sync
```

2. **Configure environment**:

```bash
cd services/registry
cp .env.example .env
# Edit .env with your configuration
```

3. **Generate Prisma client** (from monorepo root):

```bash
cd common/database
uv run prisma generate
```

4. **Run migrations**:

```bash
uv run prisma migrate dev --name init
```

5. **Generate gRPC stubs** (from monorepo root):

```bash
cd common/proto
uv run python -m grpc_tools.protoc \
  -I./src \
  --python_out=./src \
  --grpc_python_out=./src \
  ./src/registry.proto
```

## Running the Service

### Development

```bash
# From monorepo root
uv run python services/registry/src/main.py
```

The service will start:
- **REST API**: http://localhost:8000
- **gRPC Server**: localhost:50051
- **Health Monitor**: Background scheduler

### API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Public REST API

- `POST /api/v1/agents/register` - Register a new agent
- `GET /api/v1/agents` - List user's agents
- `GET /api/v1/agents/{agent_id}` - Get agent manifest
- `PUT /api/v1/agents/{agent_id}` - Update agent
- `DELETE /api/v1/agents/{agent_id}` - Delete agent
- `GET /api/v1/health` - Health check

### Internal gRPC API

- `UpdateAgentHealth` - Update agent health status
- `GetAgentManifest` - Get single agent manifest
- `GetMultipleManifests` - Get multiple manifests (batch)

## Authentication

All endpoints (except `/health`) require a PAT (Personal Access Token):

```http
Authorization: Bearer orcha_pat_xxxxxxxxxxxxxxxx
```

## Configuration

Key environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/orcha

# Server
PORT=8000
GRPC_PORT=50051

# Health Monitoring
HEALTH_CHECK_INTERVAL=300  # seconds
MAX_HEALTH_FAILURES=3

# MCP Protocol
MCP_PROTOCOL_VERSION=2025-11-25
```

## Directory Structure

```
services/registry/
├── src/
│   ├── adapters/          # Protocol adapters (MCP, A2A)
│   ├── api/              # REST endpoints
│   ├── background/       # Health monitoring
│   ├── grpc_server/      # gRPC servicer
│   ├── models/           # Pydantic models
│   ├── services/         # Business logic
│   ├── utils/            # Utilities
│   ├── config.py         # Configuration
│   └── main.py           # Entry point
├── .env.example
├── pyproject.toml
└── README.md
```

## Development

### Code Style

The project uses:
- **black** for formatting
- **ruff** for linting

### Testing

```bash
uv run pytest services/registry/tests/
```

### API Testing (Manual)

1. **Start the registry** (from monorepo root):
   ```bash
   make dev s=registry
   ```

2. **Start the manifest server** — serves agent manifests for registration:
   ```bash
   make test-manifest-server
   ```
   Runs on `http://localhost:9000`. Available fixtures are in [`services/registry/tests/fixtures/`](./tests/fixtures/) (e.g. `mcp_weather.yaml`, `a2a_logistics.yaml`). Add custom manifests there to test them.

3. **Open Swagger UI**: `http://localhost:8000/docs`

4. **Register an agent** via `POST /api/v1/agents/register`, passing a manifest URL pointing at the manifest server:
   ```
   http://localhost:9000/agents/mcp_weather.yaml
   ```

## License

[Your License]
