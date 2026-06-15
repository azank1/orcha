# Registry Microservice - Technical Specification

**Version:** 1.0.0  
**Last Updated:** January 22, 2026  
**Target Audience:** Development teams, coding agents, technical architects

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Monorepo Structure](#3-monorepo-structure)
4. [Database Schema](#4-database-schema)
5. [REST API Specification](#5-rest-api-specification)
6. [gRPC Service Definition](#6-grpc-service-definition)
7. [Protocol Adapters](#7-protocol-adapters)
8. [Authentication & Security](#8-authentication--security)
9. [Docker & CI/CD](#9-docker--cicd)
10. [Observability](#10-observability)
11. [Implementation Checklist](#11-implementation-checklist)

---

## 1. Overview

### 1.1 Purpose

The Registry microservice is the entry point for agent developers to register their AI agents into the Emerge ecosystem. It handles:

- Agent registration via REST API
- Protocol-agnostic harvesting (MCP, A2A)
- Manifest normalization into Universal Agent Manifest format
- Health monitoring
- Version management
- Communication with Planning and Manifest Processing services via gRPC

### 1.2 Core Responsibilities

| Responsibility | Description |
|---------------|-------------|
| **Agent Registration** | Accept registration requests, validate `emerge.yaml`, initiate harvesting |
| **Protocol Adaptation** | MCP and A2A adapter implementations for capability harvesting |
| **Data Storage** | Persist agent metadata, capabilities, security configs, payment info |
| **Health Monitoring** | Background cron job to ping agent health endpoints |
| **Version Control** | Track manifest changes across agent versions |
| **gRPC Server** | Expose internal APIs for Planning and Manifest Processing services |

### 1.3 Technology Stack

- **Language:** Python 3.12+
- **Monorepo Manager:** `uv` (Astral)
- **Web Framework:** FastAPI
- **ORM:** Prisma Client (Python)
- **Database:** Supabase PostgreSQL
- **gRPC:** `grpcio`, `grpcio-tools`
- **Containerization:** Docker with multi-stage builds
- **CI/CD:** GitHub Actions (recommended)

**Protocol Versions:**

| Protocol | Version | Specification |
|----------|---------|---------------|
| **MCP** | `2025-11-25` | https://modelcontextprotocol.io/specification/2025-11-25/schema |
| **A2A** | `1.0` | Agent Card v1.0 Schema |

### 1.4 Key Design Decisions

1. **Separate Tables (No JSONB blobs):** All complex structures stored in normalized tables
2. **Parallel Harvesting:** MCP `tools/list`, `resources/list`, `prompts/list` called concurrently
3. **Synchronous Registration:** HTTP response waits for harvesting completion (3 retries on failure)
4. **Harvested Data Wins:** If conflict between `emerge.yaml` and harvested data, harvested wins
5. **PAT Authentication:** GitHub-style Personal Access Tokens for developer auth
6. **x402 from Headers:** Payment metadata extracted from HTTP response headers during dry-run
7. **A2A Agent-Level Auth:** In A2A v1, `authSchemes` is at the root level and applies to ALL skills (no per-skill auth)
8. **MCP Session-Level Auth:** In MCP, auth is configured at transport level and applies to the entire session
9. **Protocol Version:** Use MCP spec `2025-11-25` (latest version as of Jan 2026)

---

## 2. System Architecture

### 2.1 Service Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                     Registry Microservice                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  REST API    │  │  gRPC Server │  │  Health Cron │          │
│  │  (FastAPI)   │  │              │  │  (Background)│          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│         └─────────┬───────┴──────────────────┘                   │
│                   │                                              │
│         ┌─────────▼──────────────────┐                          │
│         │  Registry Core Service     │                          │
│         │  - Validation              │                          │
│         │  - Orchestration           │                          │
│         └─────────┬──────────────────┘                          │
│                   │                                              │
│         ┌─────────┴──────────────────┐                          │
│         │                            │                          │
│    ┌────▼─────┐               ┌─────▼──────┐                   │
│    │   MCP    │               │    A2A     │                   │
│    │ Adapter  │               │  Adapter   │                   │
│    └────┬─────┘               └─────┬──────┘                   │
│         │                           │                           │
│         └───────────┬───────────────┘                           │
│                     │                                            │
│              ┌──────▼───────┐                                   │
│              │   Prisma ORM │                                   │
│              └──────┬───────┘                                   │
└─────────────────────┼────────────────────────────────────────────┘
                      │
              ┌───────▼────────┐
              │  Supabase PG   │
              └────────────────┘
```

### 2.2 Data Flow: Agent Registration

```
Developer
   │
   │ POST /api/v1/agents/register
   │ (PAT token + emerge.yaml)
   ├──────────────────────────────────────────────────────────────┐
   │                                                               │
   ▼                                                               │
┌──────────────────────┐                                          │
│  1. Validate Request │                                          │
│  - Check PAT token   │                                          │
│  - Parse emerge.yaml │                                          │
│  - Validate required │                                          │
│    fields            │                                          │
└──────┬───────────────┘                                          │
       │                                                           │
       ▼                                                           │
┌──────────────────────┐                                          │
│  2. Select Adapter   │                                          │
│  - protocol.type     │                                          │
│    "mcp" → MCP       │                                          │
│    "a2a" → A2A       │                                          │
└──────┬───────────────┘                                          │
       │                                                           │
       ▼                                                           │
┌──────────────────────┐       ┌─────────────────────┐           │
│  3. Harvest Data     │◄──────│  Retry Logic (3x)   │           │
│  - Capabilities      │       │  - Exponential back │           │
│  - Payment metadata  │       │  - 1s, 2s, 4s delay │           │
│  - Security configs  │       └─────────────────────┘           │
└──────┬───────────────┘                                          │
       │                                                           │
       ▼                                                           │
┌──────────────────────┐                                          │
│  4. Merge & Override │                                          │
│  - Harvested wins    │                                          │
│  - Generate IDs      │                                          │
│  - Add timestamps    │                                          │
└──────┬───────────────┘                                          │
       │                                                           │
       ▼                                                           │
┌──────────────────────┐                                          │
│  5. Save to DB       │                                          │
│  - Agent record      │                                          │
│  - Capabilities      │                                          │
│  - Auth strategies   │                                          │
│  - Payment configs   │                                          │
│  - Version record    │                                          │
└──────┬───────────────┘                                          │
       │                                                           │
       ▼                                                           │
┌──────────────────────┐                                          │
│  6. Notify Services  │                                          │
│  - gRPC call to      │                                          │
│    Planning service  │                                          │
│  - gRPC call to      │                                          │
│    Manifest service  │                                          │
└──────┬───────────────┘                                          │
       │                                                           │
       │ HTTP 201 Created                                         │
       │ { "agent_id": "...", "status": "registered" }            │
       └──────────────────────────────────────────────────────────┘
```

---

## 3. Monorepo Structure

Following `uv` workspace conventions:

```
emerge-monorepo/
├── pyproject.toml                  # Workspace root
├── uv.lock                         # Single lockfile for all services
├── .venv/                          # Unified virtualenv
│
├── common/                         # Shared libraries
│   ├── database/                   # Database as a library
│   │   ├── pyproject.toml
│   │   ├── schema.prisma           # Single source of truth
│   │   ├── migrations/             # Prisma migrations
│   │   ├── seeds/                  # Seed data scripts
│   │   └── src/
│   │       ├── __init__.py
│   │       └── generated_client/   # Prisma output
│   │
│   ├── proto/                      # Shared protobuf definitions
│   │   ├── pyproject.toml
│   │   └── src/
│   │       ├── __init__.py
│   │       ├── registry.proto
│   │       ├── planning.proto
│   │       └── manifest.proto
│   │
│   └── utils/                      # Common utilities
│       ├── pyproject.toml
│       └── src/
│           ├── __init__.py
│           ├── auth.py
│           ├── retry.py
│           └── logging_config.py
│
├── services/
│   ├── registry/                   # THIS SERVICE
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   ├── .env.example
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── main.py             # FastAPI app entry point
│   │   │   ├── config.py           # Settings (Pydantic BaseSettings)
│   │   │   ├── api/                # REST endpoints
│   │   │   │   ├── __init__.py
│   │   │   │   ├── v1/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── agents.py   # /api/v1/agents/*
│   │   │   │   │   └── health.py   # /api/v1/health/*
│   │   │   ├── grpc_server/        # Internal gRPC
│   │   │   │   ├── __init__.py
│   │   │   │   └── registry_servicer.py
│   │   │   ├── adapters/           # Protocol adapters
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py         # Abstract adapter
│   │   │   │   ├── mcp.py          # MCP implementation
│   │   │   │   └── a2a.py          # A2A implementation
│   │   │   ├── services/           # Business logic
│   │   │   │   ├── __init__.py
│   │   │   │   ├── registration.py
│   │   │   │   ├── validation.py
│   │   │   │   ├── health_check.py
│   │   │   │   └── version_manager.py
│   │   │   ├── models/             # Pydantic models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── emerge_config.py    # emerge.yaml structure
│   │   │   │   ├── universal_manifest.py
│   │   │   │   └── api_responses.py
│   │   │   ├── background/         # Cron jobs
│   │   │   │   ├── __init__.py
│   │   │   │   └── health_monitor.py
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       └── x402_parser.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_mcp_adapter.py
│   │       ├── test_a2a_adapter.py
│   │       └── test_registration.py
│   │
│   ├── planning/                   # Future service
│   └── manifest-processor/         # Future service
│
├── docker-compose.yml              # Local dev environment
└── .github/
    └── workflows/
        └── ci.yml                  # CI/CD pipeline
```

### 3.1 Workspace Configuration

**Root `pyproject.toml`:**

```toml
[project]
name = "emerge-monorepo"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[tool.uv.workspace]
members = ["services/*", "common/*"]
```

**`common/database/pyproject.toml`:**

```toml
[project]
name = "common-database"
version = "0.1.0"
dependencies = [
    "prisma>=0.11.0",
    "asyncpg>=0.29.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**`common/proto/pyproject.toml`:**

```toml
[project]
name = "common-proto"
version = "0.1.0"
dependencies = [
    "grpcio>=1.60.0",
    "grpcio-tools>=1.60.0",
    "protobuf>=4.25.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**`services/registry/pyproject.toml`:**

```toml
[project]
name = "registry-service"
version = "0.1.0"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "httpx>=0.26.0",
    "pyyaml>=6.0.1",
    "common-database",
    "common-proto",
    "common-utils",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "black>=23.12.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 3.2 Development Workflow

```bash
# 1. Install all dependencies (from root)
uv sync

# 2. Generate Prisma client
cd common/database
uv run prisma generate

# 3. Run migrations (development)
uv run prisma migrate dev --name init

# 4. Generate gRPC stubs
cd ../../common/proto
uv run python -m grpc_tools.protoc \
  -I./src \
  --python_out=./src \
  --grpc_python_out=./src \
  ./src/*.proto

# 5. Run Registry service (from root)
uv run python services/registry/src/main.py

# 6. Run tests
uv run pytest services/registry/tests/
```

---

## 4. Database Schema

### 4.1 Prisma Schema

**File:** `common/database/schema.prisma`

```prisma
generator client {
  provider             = "prisma-client-py"
  output               = "./src/generated_client"
  recursive_type_depth = 5
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// ============================================================================
// USER MANAGEMENT
// ============================================================================

model User {
  id            String    @id @default(cuid())
  email         String    @unique
  username      String?   @unique
  pat_token_hash String   // bcrypt hash of Personal Access Token
  created_at    DateTime  @default(now())
  updated_at    DateTime  @updatedAt
  is_active     Boolean   @default(true)
  
  // Relations
  agents        Agent[]
  
  @@map("users")
}

// ============================================================================
// AGENT REGISTRY
// ============================================================================

model Agent {
  id                String      @id // DID format: did:emerge:agent:xyz
  user_id           String
  name              String
  version           String
  description       String      @db.Text
  provider          String
  owner_contact     String
  tags              String[]    // Array of strings
  
  // Protocol
  protocol_type     ProtocolType  // Enum: MCP, A2A
  protocol_version  String
  
  // Health
  health_status     HealthStatus  @default(UNKNOWN)  // Enum
  health_endpoint   String
  last_health_check DateTime?
  health_failures   Int          @default(0)
  
  // Metadata
  indexed_at        DateTime     @default(now())
  updated_at        DateTime     @updatedAt
  is_active         Boolean      @default(true)
  
  // Relations
  user              User         @relation(fields: [user_id], references: [id], onDelete: Cascade)
  transport         Transport?
  security          Security?
  payment           Payment?
  capabilities      Capability[]
  versions          AgentVersion[]
  
  @@unique([user_id, name, version])
  @@index([user_id])
  @@index([protocol_type])
  @@index([health_status])
  @@map("agents")
}

enum ProtocolType {
  MCP
  A2A
}

enum HealthStatus {
  HEALTHY
  UNHEALTHY
  UNKNOWN
}

// ============================================================================
// VERSIONING
// ============================================================================

model AgentVersion {
  id                    String   @id @default(cuid())
  agent_id              String
  version               String
  manifest_snapshot     Json     // Full snapshot of capabilities, security, payment at this version
  change_summary        String?  @db.Text
  created_at            DateTime @default(now())
  
  // Relations
  agent                 Agent    @relation(fields: [agent_id], references: [id], onDelete: Cascade)
  
  @@unique([agent_id, version])
  @@index([agent_id])
  @@map("agent_versions")
}

// ============================================================================
// PROTOCOL CONFIGURATION
// ============================================================================

model Transport {
  id            String       @id @default(cuid())
  agent_id      String       @unique
  type          TransportType  // Enum: SSE, STDIO, HTTP
  endpoint      String?      // Required for SSE/HTTP
  command       String?      // Required for STDIO
  args          String[]     // For STDIO
  
  // Relations
  agent         Agent        @relation(fields: [agent_id], references: [id], onDelete: Cascade)
  
  @@map("transports")
}

enum TransportType {
  SSE
  STDIO
  HTTP
}

// ============================================================================
// SECURITY & AUTHENTICATION
// ============================================================================

model Security {
  id                    String          @id @default(cuid())
  agent_id              String          @unique
  transport_layer_type  TLSType         // Enum: TLS, MTLS, NONE
  mtls_cert_vault_key   String?
  mtls_key_vault_key    String?
  mtls_ca_vault_key     String?
  
  // Relations
  agent                 Agent           @relation(fields: [agent_id], references: [id], onDelete: Cascade)
  auth_strategies       AuthStrategy[]
  
  @@map("security_configs")
}

enum TLSType {
  TLS
  MTLS
  NONE
}

model AuthStrategy {
  id                           String       @id @default(cuid())
  security_id                  String
  capability_id                String?      // NULL = applies to all, else specific capability
  
  strategy_id                  String       // User-defined ID (e.g., "strategy_api_key")
  type                         AuthType     // Enum
  
  // Config varies by type (stored as JSON for flexibility)
  config                       Json         // { "header_name": "...", "key_vault_ref": "...", etc. }
  
  // Relations
  security                     Security     @relation(fields: [security_id], references: [id], onDelete: Cascade)
  capability                   Capability?  @relation(fields: [capability_id], references: [id], onDelete: Cascade)
  
  @@index([security_id])
  @@index([capability_id])
  @@map("auth_strategies")
}

enum AuthType {
  X_API_KEY
  HTTP_BEARER
  OAUTH2
  OAUTH2_DCR
}

// ============================================================================
// PAYMENT
// ============================================================================

model Payment {
  id                    String       @id @default(cuid())
  agent_id              String       @unique
  type                  PaymentType  @default(NONE)  // Enum: X402, NONE
  enabled               Boolean      @default(false)
  chain_id              String?      // e.g., "eip155:8453"
  recipient_address     String?
  asset                 String?      // e.g., "USDC"
  token_address         String?
  default_price         String?      // Stored as string to avoid float precision issues
  currency              String?
  facilitator_url       String?      // Injected by us
  
  // Relations
  agent                 Agent        @relation(fields: [agent_id], references: [id], onDelete: Cascade)
  
  @@map("payment_configs")
}

enum PaymentType {
  X402
  NONE
}

// ============================================================================
// CAPABILITIES
// ============================================================================

model Capability {
  id                    String           @id @default(cuid())
  agent_id              String
  
  type                  CapabilityType   // Enum: TOOL, RESOURCE, PROMPT
  capability_id         String           // Tool/resource/prompt ID from agent
  name                  String
  description           String           @db.Text
  
  // Type-specific fields (nullable for irrelevant types)
  input_schema          Json?            // For TOOL
  output_schema         Json?            // For TOOL
  uri_template          String?          // For RESOURCE
  mime_type             String?          // For RESOURCE
  arguments             Json?            // For PROMPT (array of arg objects)
  
  // Per-capability overrides
  x402_price            String?          // Override default agent price
  x402_asset            String?          // Override default asset
  
  // Relations
  agent                 Agent            @relation(fields: [agent_id], references: [id], onDelete: Cascade)
  auth_strategies       AuthStrategy[]   // A2A agents can have per-capability auth
  
  @@unique([agent_id, capability_id])
  @@index([agent_id])
  @@index([type])
  @@map("capabilities")
}

enum CapabilityType {
  TOOL
  RESOURCE
  PROMPT
}
```

### 4.2 Migration Strategy

**Initial Migration:**

```bash
cd common/database
uv run prisma migrate dev --name initial_schema
```

**Subsequent Migrations:**

```bash
# After schema changes
uv run prisma migrate dev --name add_new_field

# Production deployment (apply only)
uv run prisma migrate deploy
```

### 4.3 Seed Data

**File:** `common/database/seeds/main.py`

```python
import asyncio
import bcrypt
from prisma import Prisma

async def seed_users():
    """Create test users with PAT tokens."""
    db = Prisma()
    await db.connect()
    
    # Test user
    test_token = "emerge_pat_test123456789"
    hashed_token = bcrypt.hashpw(test_token.encode(), bcrypt.gensalt()).decode()
    
    user = await db.user.create(
        data={
            "email": "developer@example.com",
            "username": "testdev",
            "pat_token_hash": hashed_token,
        }
    )
    
    print(f"✓ Created user: {user.email}")
    print(f"  PAT Token: {test_token}")
    
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(seed_users())
```

**Run Seeds:**

```bash
cd common/database
uv run python seeds/main.py
```

---

## 5. REST API Specification

### 5.1 Base URL

- **Local Development:** `http://localhost:8000/api/v1`
- **Production:** `https://registry.emerge.bot/api/v1`

### 5.2 Authentication

All endpoints require a `Bearer` token in the `Authorization` header:

```http
Authorization: Bearer emerge_pat_xxxxxxxxxxxxxxxx
```

**Token Format:**
- Prefix: `emerge_pat_`
- Length: 40 characters total
- Example: `emerge_pat_abc123def456ghi789jkl012`

**Validation:**
- Extract token from header
- Query `users` table for matching `pat_token_hash` using bcrypt
- If invalid: Return `401 Unauthorized`

### 5.3 Endpoints

#### 5.3.1 Register Agent

**Endpoint:** `POST /agents/register`

**Description:** Registers a new agent by validating the `emerge.yaml` config, harvesting capabilities, and storing the Universal Agent Manifest.

**Request:**

```http
POST /api/v1/agents/register
Content-Type: multipart/form-data
Authorization: Bearer emerge_pat_xxxxxxxxxxxxxxxx

emerge_yaml: <file>
```

**`emerge.yaml` Structure:**

```yaml
identity:
  id: "did:emerge:agent:my-agent-01"
  name: "MyAwesomeAgent"
  version: "1.0.0"
  description: "A powerful financial analysis agent"
  tags: ["finance", "trading", "analytics"]

protocol:
  type: "mcp"  # or "a2a"
  version: "2024-11-05"
  transport:
    type: "sse"  # or "stdio" or "http"
    endpoint: "https://api.example.com/mcp/sse"
    # For stdio:
    # command: "npx"
    # args: ["-y", "@modelcontextprotocol/server-filesystem", "/path"]

health_endpoint: "https://api.example.com/health"

security:
  transport_layer:
    type: "tls"  # or "mtls" or "none"
    # If mtls:
    # mtls_config:
    #   cert_vault_key: "AGENT_CERT_XYZ"
    #   key_vault_key: "AGENT_KEY_XYZ"
    #   ca_vault_key: "AGENT_CA_XYZ"
  
  auth_strategies:
    - id: "strategy_api_key"
      type: "x_api_key"
      config:
        header_name: "X-Api-Key"
        key_vault_ref: "MY_API_KEY"
    
    - id: "strategy_oauth"
      type: "oauth2"
      config:
        oidc_discovery_url: "https://accounts.google.com/.well-known/openid-configuration"
        scopes: ["profile", "email"]
        provider_hint: "google"

payment:
  type: "x402"  # or "none"
  config:
    enabled: true
    chain_id: "eip155:8453"
    recipient_address: "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    asset: "USDC"
    token_address: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    default_price: "50"
    currency: "USDC"
```

**Response (Success):**

```json
{
  "status": "success",
  "data": {
    "agent_id": "did:emerge:agent:my-agent-01",
    "name": "MyAwesomeAgent",
    "version": "1.0.0",
    "registered_at": "2026-01-22T10:30:00Z",
    "health_status": "healthy",
    "capabilities_harvested": {
      "tools": 5,
      "resources": 2,
      "prompts": 1
    }
  }
}
```

**Response (Failure - Unreachable Endpoint):**

```json
{
  "status": "error",
  "error": {
    "code": "ENDPOINT_UNREACHABLE",
    "message": "Failed to reach agent endpoint after 3 retries",
    "details": {
      "endpoint": "https://api.example.com/mcp/sse",
      "last_error": "Connection timeout"
    }
  }
}
```

**Response (Failure - Validation Error):**

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid emerge.yaml configuration",
    "details": {
      "field": "identity.id",
      "reason": "Must start with 'did:emerge:agent:'"
    }
  }
}
```

**Status Codes:**
- `201 Created` - Registration successful
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Invalid PAT token
- `409 Conflict` - Agent with same ID/version already exists
- `503 Service Unavailable` - Agent endpoint unreachable after retries

---

#### 5.3.2 Get Agent Manifest

**Endpoint:** `GET /agents/{agent_id}`

**Description:** Retrieves the full Universal Agent Manifest for a registered agent.

**Request:**

```http
GET /api/v1/agents/did:emerge:agent:my-agent-01
Authorization: Bearer emerge_pat_xxxxxxxxxxxxxxxx
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "identity": {
      "id": "did:emerge:agent:my-agent-01",
      "name": "MyAwesomeAgent",
      "version": "1.0.0",
      "provider": "EmergeLabs",
      "owner_contact": "developer@example.com",
      "description": "A powerful financial analysis agent",
      "tags": ["finance", "trading", "analytics"]
    },
    "metadata": {
      "indexed_at": "2026-01-22T10:30:00Z",
      "health_status": "healthy",
      "health_endpoint": "https://api.example.com/health"
    },
    "protocol": {
      "type": "mcp",
      "version": "2024-11-05",
      "transport": {
        "type": "sse",
        "endpoint": "https://api.example.com/mcp/sse"
      }
    },
    "security": {
      "transport_layer": {
        "type": "tls"
      },
      "auth_strategies": [
        {
          "id": "strategy_api_key",
          "type": "x_api_key",
          "config": {
            "header_name": "X-Api-Key",
            "key_vault_ref": "MY_API_KEY"
          }
        }
      ]
    },
    "payment": {
      "type": "x402",
      "config": {
        "enabled": true,
        "chain_id": "eip155:8453",
        "recipient_address": "0x742d35...",
        "asset": "USDC",
        "default_price": "50",
        "facilitator_url": "https://api.emerge.bot/verify"
      }
    },
    "capabilities": [
      {
        "type": "tool",
        "id": "get_stock_price",
        "name": "Get Stock Price",
        "description": "Fetches current stock price for a symbol",
        "input_schema": {
          "type": "object",
          "properties": {
            "symbol": {"type": "string"}
          },
          "required": ["symbol"]
        },
        "payment": {
          "price": "10",
          "asset": "USDC"
        }
      }
    ]
  }
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Invalid PAT
- `404 Not Found` - Agent doesn't exist

---

#### 5.3.3 List User's Agents

**Endpoint:** `GET /agents`

**Description:** Lists all agents registered by the authenticated user.

**Request:**

```http
GET /api/v1/agents?page=1&limit=20&status=healthy
Authorization: Bearer emerge_pat_xxxxxxxxxxxxxxxx
```

**Query Parameters:**
- `page` (int, default: 1)
- `limit` (int, default: 20, max: 100)
- `status` (optional): Filter by health status (`healthy`, `unhealthy`, `unknown`)
- `protocol` (optional): Filter by protocol type (`mcp`, `a2a`)

**Response:**

```json
{
  "status": "success",
  "data": {
    "agents": [
      {
        "id": "did:emerge:agent:my-agent-01",
        "name": "MyAwesomeAgent",
        "version": "1.0.0",
        "health_status": "healthy",
        "protocol_type": "mcp",
        "indexed_at": "2026-01-22T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "total_pages": 1
    }
  }
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Invalid PAT

---

#### 5.3.4 Update Agent

**Endpoint:** `PUT /agents/{agent_id}`

**Description:** Updates an existing agent (creates new version if version number changes).

**Request:**

```http
PUT /api/v1/agents/did:emerge:agent:my-agent-01
Content-Type: multipart/form-data
Authorization: Bearer emerge_pat_xxxxxxxxxxxxxxxx

emerge_yaml: <file>
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "agent_id": "did:emerge:agent:my-agent-01",
    "version": "1.1.0",
    "updated_at": "2026-01-22T11:00:00Z",
    "version_created": true
  }
}
```

**Status Codes:**
- `200 OK` - Updated existing version
- `201 Created` - New version created
- `401 Unauthorized` - Invalid PAT
- `403 Forbidden` - Not owner of agent
- `404 Not Found` - Agent doesn't exist

---

#### 5.3.5 Delete Agent

**Endpoint:** `DELETE /agents/{agent_id}`

**Description:** Soft-deletes an agent (sets `is_active = false`).

**Request:**

```http
DELETE /api/v1/agents/did:emerge:agent:my-agent-01
Authorization: Bearer emerge_pat_xxxxxxxxxxxxxxxx
```

**Response:**

```json
{
  "status": "success",
  "message": "Agent deleted successfully"
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Invalid PAT
- `403 Forbidden` - Not owner
- `404 Not Found` - Agent doesn't exist

---

#### 5.3.6 Health Check

**Endpoint:** `GET /health`

**Description:** Registry service health check (no auth required).

**Request:**

```http
GET /api/v1/health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-22T10:30:00Z",
  "database": "connected",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - Healthy
- `503 Service Unavailable` - Unhealthy

---

## 6. gRPC Service Definition

### 6.1 Protocol Buffers

**File:** `common/proto/src/registry.proto`

```protobuf
syntax = "proto3";

package emerge.registry.v1;

import "google/protobuf/timestamp.proto";
import "google/protobuf/struct.proto";

// ============================================================================
// SERVICE DEFINITION
// ============================================================================

service RegistryService {
  // Internal: Called by health monitoring cron job
  rpc UpdateAgentHealth(UpdateHealthRequest) returns (UpdateHealthResponse);
  
  // Internal: Called by Planning service to query agent details
  rpc GetAgentManifest(GetManifestRequest) returns (UniversalManifest);
  
  // Internal: Batch endpoint for Planning service
  rpc GetMultipleManifests(GetMultipleManiifestsRequest) returns (GetMultipleManifestsResponse);
}

// ============================================================================
// UPDATE HEALTH
// ============================================================================

message UpdateHealthRequest {
  string agent_id = 1;
  HealthStatus status = 2;
  string last_error = 3;  // Optional error message
  google.protobuf.Timestamp checked_at = 4;
}

message UpdateHealthResponse {
  bool success = 1;
  string message = 2;
}

enum HealthStatus {
  HEALTH_STATUS_UNSPECIFIED = 0;
  HEALTH_STATUS_HEALTHY = 1;
  HEALTH_STATUS_UNHEALTHY = 2;
  HEALTH_STATUS_UNKNOWN = 3;
}

// ============================================================================
// GET MANIFEST
// ============================================================================

message GetManifestRequest {
  string agent_id = 1;
  string version = 2;  // Optional: if empty, returns latest
}

message GetMultipleManiifestsRequest {
  repeated string agent_ids = 1;
}

message GetMultipleManifestsResponse {
  repeated UniversalManifest manifests = 1;
}

// ============================================================================
// UNIVERSAL AGENT MANIFEST (Core Data Structure)
// ============================================================================

message UniversalManifest {
  IdentityInfo identity = 1;
  MetadataInfo metadata = 2;
  ProtocolInfo protocol = 3;
  SecurityInfo security = 4;
  PaymentInfo payment = 5;
  repeated Capability capabilities = 6;
}

message IdentityInfo {
  string id = 1;  // DID format
  string name = 2;
  string version = 3;
  string provider = 4;
  string owner_contact = 5;
  string description = 6;
  repeated string tags = 7;
}

message MetadataInfo {
  google.protobuf.Timestamp indexed_at = 1;
  HealthStatus health_status = 2;
  string health_endpoint = 3;
}

message ProtocolInfo {
  string type = 1;  // "mcp" or "a2a"
  string version = 2;
  TransportInfo transport = 3;
}

message TransportInfo {
  string type = 1;  // "sse", "stdio", "http"
  string endpoint = 2;  // For sse/http
  string command = 3;   // For stdio
  repeated string args = 4;  // For stdio
}

message SecurityInfo {
  TransportLayerSecurity transport_layer = 1;
  repeated AuthStrategy auth_strategies = 2;
}

message TransportLayerSecurity {
  string type = 1;  // "tls", "mtls", "none"
  MTLSConfig mtls_config = 2;  // Only if type="mtls"
}

message MTLSConfig {
  string cert_vault_key = 1;
  string key_vault_key = 2;
  string ca_vault_key = 3;
}

message AuthStrategy {
  string id = 1;
  string type = 2;  // "x_api_key", "http_bearer", "oauth2", "oauth2_dcr"
  google.protobuf.Struct config = 3;  // Flexible JSON structure
}

message PaymentInfo {
  string type = 1;  // "x402" or "none"
  PaymentConfig config = 2;
}

message PaymentConfig {
  bool enabled = 1;
  string chain_id = 2;
  string recipient_address = 3;
  string asset = 4;
  string token_address = 5;
  string default_price = 6;
  string currency = 7;
  string facilitator_url = 8;
}

message Capability {
  string type = 1;  // "tool", "resource", "prompt"
  string id = 2;
  string name = 3;
  string description = 4;
  
  // Type-specific fields (only populated if relevant)
  google.protobuf.Struct input_schema = 5;   // For tools
  google.protobuf.Struct output_schema = 6;  // For tools
  string uri_template = 7;                   // For resources
  string mime_type = 8;                      // For resources
  google.protobuf.Struct arguments = 9;      // For prompts
  
  // Payment overrides
  string x402_price = 10;
  string x402_asset = 11;
  
  // A2A: Per-capability auth
  repeated AuthStrategy auth_strategies = 12;
}
```

### 6.2 Generating Python Stubs

```bash
cd common/proto
uv run python -m grpc_tools.protoc \
  -I./src \
  --python_out=./src \
  --grpc_python_out=./src \
  ./src/registry.proto
```

This generates:
- `registry_pb2.py` (message classes)
- `registry_pb2_grpc.py` (service stubs)

### 6.3 gRPC Server Implementation

**File:** `services/registry/src/grpc_server/registry_servicer.py`

```python
import grpc
from common.proto.src import registry_pb2, registry_pb2_grpc
from common.database.src.generated_client import Prisma
from google.protobuf.timestamp_pb2 import Timestamp

class RegistryServicer(registry_pb2_grpc.RegistryServiceServicer):
    def __init__(self, db: Prisma):
        self.db = db
    
    async def UpdateAgentHealth(
        self,
        request: registry_pb2.UpdateHealthRequest,
        context: grpc.aio.ServicerContext
    ) -> registry_pb2.UpdateHealthResponse:
        """Update agent health status (called by cron job)."""
        try:
            # Map proto enum to Prisma enum
            status_map = {
                registry_pb2.HEALTH_STATUS_HEALTHY: "HEALTHY",
                registry_pb2.HEALTH_STATUS_UNHEALTHY: "UNHEALTHY",
                registry_pb2.HEALTH_STATUS_UNKNOWN: "UNKNOWN",
            }
            
            await self.db.agent.update(
                where={"id": request.agent_id},
                data={
                    "health_status": status_map[request.status],
                    "last_health_check": request.checked_at.ToDatetime(),
                    "health_failures": {
                        "increment": 1 if request.status == registry_pb2.HEALTH_STATUS_UNHEALTHY else 0
                    }
                }
            )
            
            return registry_pb2.UpdateHealthResponse(
                success=True,
                message="Health updated successfully"
            )
        except Exception as e:
            return registry_pb2.UpdateHealthResponse(
                success=False,
                message=f"Error: {str(e)}"
            )
    
    async def GetAgentManifest(
        self,
        request: registry_pb2.GetManifestRequest,
        context: grpc.aio.ServicerContext
    ) -> registry_pb2.UniversalManifest:
        """Retrieve full agent manifest."""
        agent = await self.db.agent.find_unique(
            where={"id": request.agent_id},
            include={
                "transport": True,
                "security": {"include": {"auth_strategies": True}},
                "payment": True,
                "capabilities": {"include": {"auth_strategies": True}},
            }
        )
        
        if not agent:
            context.abort(grpc.StatusCode.NOT_FOUND, "Agent not found")
        
        # Convert to protobuf (see helper function below)
        return self._agent_to_proto(agent)
    
    def _agent_to_proto(self, agent) -> registry_pb2.UniversalManifest:
        """Convert Prisma agent to protobuf message."""
        # Implementation: Map all fields from agent model to proto
        # This is tedious but straightforward - see full implementation in codebase
        pass
```

### 6.4 Starting gRPC Server

**File:** `services/registry/src/main.py`

```python
import asyncio
import grpc
from fastapi import FastAPI
from common.proto.src import registry_pb2_grpc
from grpc_server.registry_servicer import RegistryServicer
from common.database.src.generated_client import Prisma

app = FastAPI()
db = Prisma()

async def serve_grpc():
    """Start gRPC server on port 50051."""
    server = grpc.aio.server()
    registry_pb2_grpc.add_RegistryServiceServicer_to_server(
        RegistryServicer(db), server
    )
    server.add_insecure_port('[::]:50051')
    await server.start()
    print("✓ gRPC server started on port 50051")
    await server.wait_for_termination()

@app.on_event("startup")
async def startup():
    await db.connect()
    asyncio.create_task(serve_grpc())

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()
```

---

## 7. Protocol Adapters

### 7.0 Critical Understanding: Authentication in MCP vs A2A

**This section is essential reading before implementing adapters.**

#### A2A v1: Agent-Level Authentication

Based on the official A2A v1 Agent Card specification, authentication works as follows:

**Schema Structure:**
```json
{
  "authSchemes": [  // ← TOP-LEVEL (applies to ALL skills)
    {
      "scheme": "apiKey",
      "description": "Use your API key",
      "service_identifier": "my-service"
    },
    {
      "scheme": "oauth2",
      "tokenUrl": "https://auth.example.com/token",
      "scopes": ["read", "write"],
      "service_identifier": "my-oauth"
    }
  ],
  "skills": [  // ← NO auth info here
    {
      "id": "get_weather",
      "name": "Get Weather",
      "input_schema": {...}
    }
  ]
}
```

**Key Points:**
1. **ALL skills use the SAME auth mechanism** - there is no per-skill auth in A2A v1
2. The `authSchemes` array is at the **agent root level**
3. Clients must **pick ONE scheme** from the array and use it for all skill invocations
4. Skills themselves contain NO auth information

**How Clients Select Auth:**
- Client examines the `authSchemes[]` array
- Client selects one scheme (e.g., based on user preference or what credentials are available)
- That scheme is used for ALL requests to ALL skills

**Example Flow:**
```
1. Fetch Agent Card from /.well-known/agent.json
2. See authSchemes: ["apiKey", "oauth2", "bearer"]
3. Client selects "oauth2"
4. Client obtains OAuth token
5. ALL subsequent skill calls use that OAuth token
```

#### MCP: Session-Level Authentication

In MCP (Model Context Protocol), authentication is configured at the **transport level**:

```yaml
# MCP transport configuration
security:
  transport_layer:
    type: "tls"
  auth_strategies:
    - id: "strategy_api_key"
      type: "x_api_key"
      config:
        header_name: "X-API-Key"
```

**Key Points:**
1. Auth is configured once when establishing the connection
2. Single auth mechanism for the entire MCP session
3. All `tools/list`, `resources/list`, `prompts/list` calls use same auth
4. No per-tool or per-resource authentication

#### Comparison Table

| Aspect | MCP | A2A v1 |
|--------|-----|--------|
| **Auth Scope** | Session-level (transport) | Agent-level (all skills) |
| **Auth Location** | Transport config in `emerge.yaml` | `authSchemes[]` in Agent Card |
| **Discovery** | Via JSON-RPC after connection | Via `/.well-known/agent.json` |
| **Client Choice** | N/A (pre-configured) | Client picks ONE from array |
| **Per-Capability Auth** | ❌ No | ❌ No (not in v1) |
| **Multiple Auth Options** | ❌ Single mechanism | ✅ Can offer multiple schemes |

#### Implications for Registry

**For A2A Harvesting:**
- Harvest `authSchemes[]` from Agent Card root
- Store auth strategies at **agent level** in database
- Do NOT attempt to extract per-skill auth (doesn't exist in v1)
- All capabilities reference the same agent-level auth

**For MCP Harvesting:**
- Auth is already provided in `emerge.yaml` transport config
- No need to harvest auth from protocol
- Auth is session-level, not per-tool

---

### 7.1 Adapter Interface

**File:** `services/registry/src/adapters/base.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel

class CapabilityData(BaseModel):
    """Normalized capability structure."""
    type: str  # "tool", "resource", "prompt"
    id: str
    name: str
    description: str
    input_schema: Dict[str, Any] | None = None
    output_schema: Dict[str, Any] | None = None
    uri_template: str | None = None
    mime_type: str | None = None
    arguments: List[Dict[str, Any]] | None = None
    x402_price: str | None = None
    x402_asset: str | None = None

class HarvestResult(BaseModel):
    """Result of harvesting operation."""
    capabilities: List[CapabilityData]
    errors: List[str] = []
    metadata: Dict[str, Any] = {}  # Agent-level data (auth schemes, provider info, etc.)

class BaseAdapter(ABC):
    """Abstract base adapter for protocol-specific harvesting."""
    
    def __init__(self, endpoint: str, timeout: int = 10, max_retries: int = 3):
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_retries = max_retries
    
    @abstractmethod
    async def harvest(self) -> HarvestResult:
        """
        Harvest capabilities from agent endpoint.
        
        Returns:
            HarvestResult with capabilities and any errors encountered.
        
        Raises:
            ConnectionError: If endpoint unreachable after retries.
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if agent endpoint is healthy.
        
        Returns:
            True if healthy, False otherwise.
        """
        pass
```

### 7.2 MCP Adapter

**File:** `services/registry/src/adapters/mcp.py`  
**Protocol Version:** `2025-11-25` (Latest MCP specification)

```python
import httpx
import asyncio
from typing import Dict, Any
from .base import BaseAdapter, HarvestResult, CapabilityData

class MCPAdapter(BaseAdapter):
    """
    Adapter for MCP (Model Context Protocol) agents.
    
    Protocol Version: 2025-11-25
    Specification: https://modelcontextprotocol.io/specification/2025-11-25/schema
    """
    
    async def harvest(self) -> HarvestResult:
        """
        Harvest MCP capabilities via JSON-RPC 2.0.
        
        MCP Specification:
        - Endpoint: SSE, STDIO, or HTTP
        - Methods: tools/list, resources/list, prompts/list
        - x402 metadata: Check response headers during dry-run
        - Protocol Version: 2025-11-25
        """
        capabilities = []
        errors = []
        
        try:
            # Parallel harvest for performance
            results = await asyncio.gather(
                self._harvest_tools(),
                self._harvest_resources(),
                self._harvest_prompts(),
                return_exceptions=True
            )
            
            for result in results:
                if isinstance(result, Exception):
                    errors.append(str(result))
                else:
                    capabilities.extend(result)
            
            return HarvestResult(capabilities=capabilities, errors=errors)
        
        except Exception as e:
            raise ConnectionError(f"Failed to harvest MCP agent: {str(e)}")
    
    async def _harvest_tools(self) -> list[CapabilityData]:
        """Harvest tools via MCP tools/list."""
        tools = []
        
        # JSON-RPC 2.0 request
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await self._retry_request(client, payload)
            
            if "result" in response and "tools" in response["result"]:
                for tool in response["result"]["tools"]:
                    # Extract x402 from dry-run if not in metadata
                    x402_price, x402_asset = await self._extract_x402(
                        tool["name"], tool.get("metadata", {})
                    )
                    
                    tools.append(CapabilityData(
                        type="tool",
                        id=tool["name"],
                        name=tool["name"],
                        description=tool.get("description", ""),
                        input_schema=tool.get("inputSchema"),
                        output_schema=tool.get("outputSchema"),
                        x402_price=x402_price,
                        x402_asset=x402_asset,
                    ))
        
        return tools
    
    async def _harvest_resources(self) -> list[CapabilityData]:
        """Harvest resources via MCP resources/list."""
        resources = []
        
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list",
            "params": {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await self._retry_request(client, payload)
            
            if "result" in response and "resources" in response["result"]:
                for resource in response["result"]["resources"]:
                    resources.append(CapabilityData(
                        type="resource",
                        id=resource["uri"],
                        name=resource.get("name", resource["uri"]),
                        description=resource.get("description", ""),
                        uri_template=resource["uri"],
                        mime_type=resource.get("mimeType"),
                    ))
        
        return resources
    
    async def _harvest_prompts(self) -> list[CapabilityData]:
        """Harvest prompts via MCP prompts/list."""
        prompts = []
        
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "prompts/list",
            "params": {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await self._retry_request(client, payload)
            
            if "result" in response and "prompts" in response["result"]:
                for prompt in response["result"]["prompts"]:
                    prompts.append(CapabilityData(
                        type="prompt",
                        id=prompt["name"],
                        name=prompt["name"],
                        description=prompt.get("description", ""),
                        arguments=prompt.get("arguments", []),
                    ))
        
        return prompts
    
    async def _extract_x402(
        self, 
        tool_name: str, 
        metadata: Dict[str, Any]
    ) -> tuple[str | None, str | None]:
        """
        Extract x402 payment metadata.
        
        Priority:
        1. Check metadata.x402 field
        2. Make dry-run call and check X-Microtransaction header
        """
        # Check metadata first
        if "x402" in metadata:
            return (
                metadata["x402"].get("price"),
                metadata["x402"].get("asset")
            )
        
        # Dry-run call
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {}  # Empty args for probe
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    timeout=self.timeout,
                    headers={"X-Emerge-Dry-Run": "true"}  # Signal to agent
                )
                
                # Check for x402 header (see SDK documentation)
                if "X-Microtransaction" in response.headers:
                    # Parse: "price=10;asset=USDC;recipient=0x..."
                    header = response.headers["X-Microtransaction"]
                    parts = dict(p.split("=") for p in header.split(";"))
                    return (parts.get("price"), parts.get("asset"))
        
        except Exception:
            pass  # No x402 metadata available
        
        return (None, None)
    
    async def _retry_request(
        self, 
        client: httpx.AsyncClient, 
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Retry logic with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise ConnectionError(
                        f"Failed after {self.max_retries} attempts: {str(e)}"
                    )
                
                # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(2 ** attempt)
    
    async def health_check(self) -> bool:
        """Ping MCP server with initialize call."""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",  # Latest MCP spec
                    "capabilities": {},
                    "clientInfo": {
                        "name": "Emerge Registry",
                        "version": "1.0.0"
                    }
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    timeout=5
                )
                return response.status_code == 200
        
        except Exception:
            return False
```

### 7.3 A2A Adapter

**File:** `services/registry/src/adapters/a2a.py`

**⚠️ CRITICAL:** A2A v1 uses **agent-level auth** (not per-skill). All skills use the same auth mechanism.

#### Official A2A v1 Schema Structure

```json
{
  "authSchemes": [  // <-- TOP-LEVEL (applies to ALL skills)
    {
      "scheme": "apiKey",
      "service_identifier": "my-service"
    }
  ],
  "skills": [  // <-- NO auth info here
    {
      "id": "get_weather",
      "name": "Get Weather",
      "input_schema": {...}
    }
  ]
}
```

#### Implementation

```python
import httpx
import asyncio
from typing import Dict, Any, Optional
from .base import BaseAdapter, HarvestResult, CapabilityData

class A2AAdapter(BaseAdapter):
    """
    Adapter for A2A v1 protocol agents.
    
    Key Points:
    - authSchemes is TOP-LEVEL (not per-skill)
    - All skills use the same auth mechanism
    - Client chooses ONE scheme from authSchemes array
    """
    
    def __init__(
        self,
        endpoint: str,
        agent_card_json: Optional[Dict] = None,  # Pre-parsed from emerge.yaml
        timeout: int = 10,
        max_retries: int = 3
    ):
        """
        Initialize A2A adapter.
        
        Args:
            endpoint: Base URL (e.g., https://agent.example.com)
            agent_card_json: Optional pre-parsed Agent Card
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts
        """
        super().__init__(endpoint, timeout, max_retries)
        self.agent_card_json = agent_card_json
    
    async def harvest(self) -> HarvestResult:
        """
        Harvest A2A agent capabilities from Agent Card.
        
        Process:
        1. Fetch Agent Card (or use pre-parsed)
        2. Extract agent-level authSchemes
        3. Parse skills[] (no auth info here)
        4. Return normalized capabilities with agent-level metadata
        """
        try:
            # Fetch or use pre-parsed Agent Card
            agent_card = await self._get_agent_card()
            
            # Validate schema version
            schema_version = agent_card.get("schemaVersion")
            if schema_version != "1.0":
                return HarvestResult(
                    capabilities=[],
                    errors=[f"Unsupported schema version: {schema_version}"]
                )
            
            capabilities = []
            errors = []
            
            # Parse skills (map to tools in universal format)
            for skill in agent_card.get("skills", []):
                try:
                    cap = CapabilityData(
                        type="tool",
                        id=skill["id"],
                        name=skill["name"],
                        description=skill.get("description", ""),
                        input_schema=skill.get("input_schema"),
                        output_schema=skill.get("output_schema"),
                    )
                    capabilities.append(cap)
                except KeyError as e:
                    errors.append(f"Invalid skill: missing field {e}")
            
            # Store agent-level auth schemes in metadata
            # These apply to ALL skills, not per-capability
            harvest_metadata = {
                "agent_auth_schemes": agent_card.get("authSchemes", []),
                "agent_name": agent_card.get("name"),
                "agent_description": agent_card.get("description"),
                "agent_url": agent_card.get("url"),
                "provider": agent_card.get("provider"),
                "tags": agent_card.get("tags", []),
                "capabilities_meta": agent_card.get("capabilities", {}),
            }
            
            return HarvestResult(
                capabilities=capabilities,
                errors=errors,
                metadata=harvest_metadata
            )
        
        except Exception as e:
            raise ConnectionError(f"Failed to harvest A2A agent: {str(e)}")
    
    async def _get_agent_card(self) -> Dict[str, Any]:
        """Fetch Agent Card with retry logic."""
        # If pre-parsed from emerge.yaml, use that
        if self.agent_card_json:
            return self.agent_card_json
        
        # Otherwise, fetch from /.well-known/agent.json
        card_url = f"{self.endpoint.rstrip('/')}/.well-known/agent.json"
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(card_url, timeout=self.timeout)
                    response.raise_for_status()
                    return response.json()
            
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise ConnectionError(
                        f"Failed to fetch Agent Card after {self.max_retries} attempts: {e}"
                    )
                
                # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(2 ** attempt)
    
    async def health_check(self) -> bool:
        """Check if Agent Card is accessible."""
        try:
            card_url = f"{self.endpoint.rstrip('/')}/.well-known/agent.json"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(card_url, timeout=5)
                return response.status_code == 200
        
        except Exception:
            return False
```

#### Key Differences: A2A vs MCP

| Aspect | A2A v1 | MCP |
|--------|--------|-----|
| **Discovery** | Static Agent Card | Dynamic JSON-RPC |
| **Auth Scope** | **Agent-level** (all skills) | Session-level (transport) |
| **Auth Location** | `authSchemes[]` at root | Transport config |
| **Endpoint** | `/.well-known/agent.json` | SSE/stdio/HTTP |
| **Skills** | `skills[]` array | `tools/list` RPC call |
| **Per-Skill Auth** | ❌ Not in v1 | ❌ Not in protocol |
```

### 7.4 Adapter Factory

**File:** `services/registry/src/adapters/__init__.py`

```python
from .base import BaseAdapter
from .mcp import MCPAdapter
from .a2a import A2AAdapter

def get_adapter(protocol_type: str, endpoint: str) -> BaseAdapter:
    """Factory function to create appropriate adapter."""
    adapters = {
        "mcp": MCPAdapter,
        "a2a": A2AAdapter,
    }
    
    adapter_class = adapters.get(protocol_type.lower())
    if not adapter_class:
        raise ValueError(f"Unsupported protocol: {protocol_type}")
    
    return adapter_class(endpoint=endpoint)
```

---

## 8. Authentication & Security

### 8.1 PAT Token Generation

Developers generate PAT tokens via CLI or web interface:

```bash
emerge auth create-token --name "my-dev-machine"
```

**Output:**

```
✓ Token created successfully

Token: emerge_pat_abc123def456ghi789jkl012
Copy this token now - it will not be shown again.

Add to your environment:
export EMERGE_PAT_TOKEN="emerge_pat_abc123def456ghi789jkl012"
```

**Storage:**
- Token is hashed using `bcrypt` with cost factor 12
- Stored in `users.pat_token_hash`
- Original token never stored

### 8.2 Token Validation Middleware

**File:** `services/registry/src/api/middleware/auth.py`

```python
import bcrypt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from common.database.src.generated_client import Prisma

security = HTTPBearer()

async def validate_pat_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Prisma = None
) -> str:
    """
    Validate PAT token and return user_id.
    
    Returns:
        user_id if valid
    
    Raises:
        HTTPException 401 if invalid
    """
    token = credentials.credentials
    
    # Basic format check
    if not token.startswith("emerge_pat_"):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    # Query all users (in production, index by token prefix for efficiency)
    users = await db.user.find_many(where={"is_active": True})
    
    for user in users:
        # Constant-time comparison via bcrypt
        if bcrypt.checkpw(token.encode(), user.pat_token_hash.encode()):
            return user.id
    
    raise HTTPException(status_code=401, detail="Invalid or expired token")
```

**Usage in Endpoints:**

```python
from fastapi import APIRouter, Depends
from .middleware.auth import validate_pat_token

router = APIRouter()

@router.post("/agents/register")
async def register_agent(
    user_id: str = Depends(validate_pat_token),
    # ... other dependencies
):
    # user_id is now available
    pass
```

### 8.3 Vault Integration (Future)

**Placeholder for secure credential storage:**

Agents reference secrets via `key_vault_ref` (e.g., `"GOOGLE_API_KEY"`). Registry will integrate with:
- **HashiCorp Vault** (recommended)
- **AWS Secrets Manager**
- **Supabase Vault** (if available)

**Example Config:**

```python
# services/registry/src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    vault_url: str = "https://vault.emerge.bot"
    vault_token: str = ""
    
    # Fallback: local secrets (dev only)
    secrets: dict[str, str] = {}

settings = Settings()
```

---

## 9. Docker & CI/CD

### 9.1 Multi-Stage Dockerfile

**File:** `services/registry/Dockerfile`

```dockerfile
# ==============================================================================
# STAGE 1: Builder
# ==============================================================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Environment
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy workspace files for dependency resolution
COPY uv.lock pyproject.toml /app/
COPY common/database/pyproject.toml /app/common/database/
COPY common/proto/pyproject.toml /app/common/proto/
COPY common/utils/pyproject.toml /app/common/utils/
COPY services/registry/pyproject.toml /app/services/registry/

# Install dependencies (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy and generate Prisma client
COPY common/database /app/common/database
WORKDIR /app/common/database
RUN uv run prisma generate

# Generate gRPC stubs
COPY common/proto /app/common/proto
WORKDIR /app/common/proto
RUN uv run python -m grpc_tools.protoc \
    -I./src \
    --python_out=./src \
    --grpc_python_out=./src \
    ./src/*.proto

# Copy service code
COPY services/registry /app/services/registry
COPY common/utils /app/common/utils

# Install project
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package registry-service

# ==============================================================================
# STAGE 2: Runtime
# ==============================================================================
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy virtualenv
COPY --from=builder /app/.venv /app/.venv

# Add to PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Copy code
COPY --from=builder /app/services/registry /app/services/registry
COPY --from=builder /app/common /app/common

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health')"

# Run
CMD ["python", "services/registry/src/main.py"]
```

### 9.2 Docker Compose (Local Development)

**File:** `docker-compose.yml`

```yaml
version: '3.9'

services:
  # ===========================================================================
  # DATABASE
  # ===========================================================================
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: emerge_registry
      POSTGRES_USER: emerge
      POSTGRES_PASSWORD: develop123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U emerge -d emerge_registry"]
      interval: 5s
      timeout: 3s
      retries: 5

  # ===========================================================================
  # MIGRATOR (Runs once on startup)
  # ===========================================================================
  migrator:
    build:
      context: .
      dockerfile: services/registry/Dockerfile
    command: >
      bash -c "cd common/database && 
      uv run prisma migrate deploy && 
      uv run python seeds/main.py"
    environment:
      DATABASE_URL: postgresql://emerge:develop123@postgres:5432/emerge_registry
    depends_on:
      postgres:
        condition: service_healthy

  # ===========================================================================
  # REGISTRY SERVICE
  # ===========================================================================
  registry:
    build:
      context: .
      dockerfile: services/registry/Dockerfile
    ports:
      - "8000:8000"  # HTTP API
      - "50051:50051"  # gRPC
    environment:
      DATABASE_URL: postgresql://emerge:develop123@postgres:5432/emerge_registry
      LOG_LEVEL: info
      VAULT_URL: ""  # Empty for local dev
    depends_on:
      migrator:
        condition: service_completed_successfully
    volumes:
      # Hot-reload for development (comment out for production)
      - ./services/registry/src:/app/services/registry/src

volumes:
  postgres_data:
```

**Run:**

```bash
# Build and start
docker-compose up --build

# Stop
docker-compose down

# Reset database
docker-compose down -v
docker-compose up --build
```

### 9.3 CI/CD Pipeline (GitHub Actions)

**File:** `.github/workflows/ci.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # ===========================================================================
  # LINT & TEST
  # ===========================================================================
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Setup Python
        run: |
          uv python install 3.12
      
      - name: Install dependencies
        run: uv sync
      
      - name: Generate Prisma client
        run: |
          cd common/database
          uv run prisma generate
      
      - name: Run migrations
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db
        run: |
          cd common/database
          uv run prisma migrate deploy
      
      - name: Lint with Ruff
        run: uv run ruff check services/registry/src
      
      - name: Format check with Black
        run: uv run black --check services/registry/src
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/test_db
        run: uv run pytest services/registry/tests -v --cov=services/registry/src
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  # ===========================================================================
  # BUILD DOCKER IMAGE
  # ===========================================================================
  build:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: services/registry/Dockerfile
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ghcr.io/${{ github.repository }}/registry:latest
            ghcr.io/${{ github.repository }}/registry:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ===========================================================================
  # DEPLOY (Production)
  # ===========================================================================
  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Deploy to production
        run: |
          echo "Deploy to production infrastructure"
          # Add deployment commands (e.g., kubectl, terraform, etc.)
```

### 9.4 Service-Specific Builds (Git-Diff Optimization)

**Problem:** Building ALL services on every commit wastes CI minutes and slows deployments.

**Solution:** Use `git diff` to detect which services changed and only build/test/deploy those.

**File:** `.github/workflows/selective-build.yml`

```yaml
name: Selective Build & Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # ===========================================================================
  # DETECT CHANGES
  # ===========================================================================
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      registry: ${{ steps.changes.outputs.registry }}
      planning: ${{ steps.changes.outputs.planning }}
      manifest: ${{ steps.changes.outputs.manifest }}
      common: ${{ steps.changes.outputs.common }}
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2  # Need previous commit for diff
      
      - name: Detect Changed Services
        id: changes
        run: |
          # Registry service
          if git diff --name-only HEAD^ HEAD | grep -E '^services/registry/|^common/'; then
            echo "registry=true" >> $GITHUB_OUTPUT
          else
            echo "registry=false" >> $GITHUB_OUTPUT
          fi
          
          # Planning service
          if git diff --name-only HEAD^ HEAD | grep -E '^services/planning/|^common/'; then
            echo "planning=true" >> $GITHUB_OUTPUT
          else
            echo "planning=false" >> $GITHUB_OUTPUT
          fi
          
          # Manifest service
          if git diff --name-only HEAD^ HEAD | grep -E '^services/manifest/|^common/'; then
            echo "manifest=true" >> $GITHUB_OUTPUT
          else
            echo "manifest=false" >> $GITHUB_OUTPUT
          fi
          
          # Common library changes = rebuild all
          if git diff --name-only HEAD^ HEAD | grep -E '^common/'; then
            echo "common=true" >> $GITHUB_OUTPUT
          else
            echo "common=false" >> $GITHUB_OUTPUT
          fi

  # ===========================================================================
  # BUILD REGISTRY (Conditional)
  # ===========================================================================
  build-registry:
    needs: detect-changes
    if: needs.detect-changes.outputs.registry == 'true' || needs.detect-changes.outputs.common == 'true'
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Registry
        uses: docker/build-push-action@v5
        with:
          context: .
          file: services/registry/Dockerfile
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ghcr.io/${{ github.repository }}/registry:latest
            ghcr.io/${{ github.repository }}/registry:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Run Registry Tests
        run: |
          docker run ghcr.io/${{ github.repository }}/registry:${{ github.sha }} \
            uv run pytest services/registry/tests -v

  # ===========================================================================
  # BUILD PLANNING (Conditional)
  # ===========================================================================
  build-planning:
    needs: detect-changes
    if: needs.detect-changes.outputs.planning == 'true' || needs.detect-changes.outputs.common == 'true'
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Planning
        uses: docker/build-push-action@v5
        with:
          context: .
          file: services/planning/Dockerfile
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ghcr.io/${{ github.repository }}/planning:latest
            ghcr.io/${{ github.repository }}/planning:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ===========================================================================
  # BUILD MANIFEST (Conditional)
  # ===========================================================================
  build-manifest:
    needs: detect-changes
    if: needs.detect-changes.outputs.manifest == 'true' || needs.detect-changes.outputs.common == 'true'
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Manifest
        uses: docker/build-push-action@v5
        with:
          context: .
          file: services/manifest/Dockerfile
          push: ${{ github.event_name != 'pull_request' }}
          tags: |
            ghcr.io/${{ github.repository }}/manifest:latest
            ghcr.io/${{ github.repository }}/manifest:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ===========================================================================
  # DEPLOY (Only changed services)
  # ===========================================================================
  deploy:
    needs: [detect-changes, build-registry, build-planning, build-manifest]
    if: github.ref == 'refs/heads/main' && (success() || failure())  # Run even if some builds skipped
    runs-on: ubuntu-latest
    
    steps:
      - name: Deploy Registry
        if: needs.detect-changes.outputs.registry == 'true'
        run: |
          echo "Deploying Registry service..."
          # kubectl set image deployment/registry registry=ghcr.io/${{ github.repository }}/registry:${{ github.sha }}
      
      - name: Deploy Planning
        if: needs.detect-changes.outputs.planning == 'true'
        run: |
          echo "Deploying Planning service..."
          # kubectl set image deployment/planning planning=ghcr.io/${{ github.repository }}/planning:${{ github.sha }}
      
      - name: Deploy Manifest
        if: needs.detect-changes.outputs.manifest == 'true'
        run: |
          echo "Deploying Manifest service..."
          # kubectl set image deployment/manifest manifest=ghcr.io/${{ github.repository }}/manifest:${{ github.sha }}
```

**Alternative: Using GitHub Action (Simpler)**

Install `dorny/paths-filter` action for cleaner syntax:

```yaml
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      registry: ${{ steps.filter.outputs.registry }}
      planning: ${{ steps.filter.outputs.planning }}
      manifest: ${{ steps.filter.outputs.manifest }}
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: dorny/paths-filter@v2
        id: filter
        with:
          filters: |
            registry:
              - 'services/registry/**'
              - 'common/**'
            planning:
              - 'services/planning/**'
              - 'common/**'
            manifest:
              - 'services/manifest/**'
              - 'common/**'
  
  build-registry:
    needs: changes
    if: ${{ needs.changes.outputs.registry == 'true' }}
    # ... build steps
```

**Benefits:**
- ⚡ **Faster CI:** Only builds changed services (saves 60-80% CI time)
- 💰 **Cost Savings:** Less compute = lower GitHub Actions minutes
- 🚀 **Faster Deployments:** Only redeploys what changed
- 🐛 **Easier Debugging:** Failed builds are service-specific

---

## 10. Observability

### 10.1 Metrics

**Recommended Tool:** **Prometheus + Grafana** (cost-effective, self-hosted)

**Key Metrics to Track:**

| Metric | Type | Description | Alerting Threshold |
|--------|------|-------------|-------------------|
| `registry_registration_total` | Counter | Total agent registrations | N/A |
| `registry_registration_duration_seconds` | Histogram | Registration latency | p95 > 10s |
| `registry_harvesting_failures_total` | Counter | Failed harvesting attempts | > 10/hour |
| `registry_health_checks_total` | Counter | Total health checks performed | N/A |
| `registry_unhealthy_agents` | Gauge | Number of unhealthy agents | > 5 |
| `registry_database_connections` | Gauge | Active DB connections | > 80% of max |
| `registry_grpc_requests_total` | Counter | gRPC calls by method | N/A |
| `registry_grpc_request_duration_seconds` | Histogram | gRPC latency | p95 > 1s |
| `registry_http_requests_total` | Counter | HTTP requests by endpoint/status | N/A |
| `registry_http_request_duration_seconds` | Histogram | HTTP latency | p95 > 2s |

**Implementation:**

```bash
uv add prometheus-client prometheus-fastapi-instrumentator
```

**File:** `services/registry/src/main.py`

```python
from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()

# Metrics
registration_counter = Counter(
    'registry_registration_total',
    'Total agent registrations',
    ['status']
)

registration_duration = Histogram(
    'registry_registration_duration_seconds',
    'Registration duration',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

unhealthy_agents = Gauge(
    'registry_unhealthy_agents',
    'Number of unhealthy agents'
)

# Auto-instrument FastAPI
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

@app.post("/api/v1/agents/register")
async def register_agent(...):
    with registration_duration.time():
        try:
            # ... registration logic ...
            registration_counter.labels(status='success').inc()
        except Exception:
            registration_counter.labels(status='failure').inc()
            raise
```

### 10.2 Logging

**Recommended Tool:** **Loki + Grafana** (cost-effective, integrates with Prometheus)

**Structured Logging:**

```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Usage
logger.info(
    "agent_registered",
    agent_id="did:emerge:agent:xyz",
    user_id="user_123",
    protocol="mcp",
    capabilities_count=5,
    duration_ms=1234
)
```

**Log Levels:**
- **DEBUG:** Detailed harvesting steps
- **INFO:** Successful operations (registrations, health checks)
- **WARNING:** Retries, non-critical failures
- **ERROR:** Failed registrations, database errors
- **CRITICAL:** Service-wide failures

### 10.3 Distributed Tracing

**Recommended Tool:** **Jaeger** (open-source, CNCF project)

**Implementation:**

```bash
uv add opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-jaeger
```

**File:** `services/registry/src/main.py`

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Manual spans
tracer = trace.get_tracer(__name__)

async def harvest_capabilities(adapter):
    with tracer.start_as_current_span("harvest_capabilities") as span:
        span.set_attribute("protocol", adapter.__class__.__name__)
        result = await adapter.harvest()
        span.set_attribute("capabilities_count", len(result.capabilities))
        return result
```

**Key Spans to Trace:**
- `registration_request` (root span)
  - `validate_config`
  - `harvest_capabilities`
    - `harvest_mcp_tools`
    - `harvest_mcp_resources`
    - `harvest_mcp_prompts`
  - `save_to_database`
  - `notify_planning_service` (gRPC call)

### 10.4 Alerts

**Recommended Tool:** **Alertmanager** (part of Prometheus ecosystem)

**Critical Alerts:**

```yaml
# prometheus-alerts.yml
groups:
  - name: registry_alerts
    interval: 1m
    rules:
      - alert: HighRegistrationLatency
        expr: histogram_quantile(0.95, registry_registration_duration_seconds) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Registration latency too high"
          description: "95th percentile registration time is {{ $value }}s"
      
      - alert: DatabaseConnectionPoolExhausted
        expr: registry_database_connections / registry_database_max_connections > 0.8
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
      
      - alert: HighUnhealthyAgentCount
        expr: registry_unhealthy_agents > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $value }} agents are unhealthy"
      
      - alert: ServiceDown
        expr: up{job="registry"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Registry service is down"
```

### 10.5 Observability Stack (Docker Compose)

**File:** `docker-compose.observability.yml`

```yaml
version: '3.9'

services:
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
  
  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./observability/grafana-dashboards:/etc/grafana/provisioning/dashboards
  
  # Loki (logs)
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./observability/loki-config.yml:/etc/loki/local-config.yaml
  
  # Jaeger (traces)
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "6831:6831/udp"  # Agent
    environment:
      COLLECTOR_ZIPKIN_HOST_PORT: 9411

volumes:
  prometheus_data:
  grafana_data:
```

### 10.6 Cost Estimation

**Monthly Costs (assuming 1000 agents, 10k registrations/month):**

| Component | Tool | Cost | Notes |
|-----------|------|------|-------|
| **Database** | Supabase Pro | $25/mo | 8GB DB, 100GB bandwidth |
| **Compute** | Fly.io (2x shared-cpu-1x) | $10/mo | 2 instances for HA |
| **Monitoring** | Self-hosted (Prometheus/Grafana) | $0 | Included in compute |
| **Logs** | Loki (self-hosted) | $5/mo | Storage only |
| **Traces** | Jaeger (self-hosted) | $0 | Sampling: 10% |
| **Alerting** | Alertmanager | $0 | Self-hosted |
| **Total** | | **~$40/mo** | |

**Alternative (Managed):**
- Datadog: ~$150/mo (for same workload)
- New Relic: ~$100/mo
- Sentry (errors only): ~$26/mo

**Recommendation:** Start with self-hosted Prometheus/Grafana/Loki/Jaeger. Migrate to Datadog/New Relic if team lacks DevOps expertise.

---

## 11. Implementation Checklist

### Phase 1: Foundation (Week 1)

- [ ] Setup monorepo structure with `uv`
- [ ] Create Prisma schema
- [ ] Setup Supabase PostgreSQL instance
- [ ] Run initial migration
- [ ] Create seed data (test users)
- [ ] Setup Docker Compose for local dev
- [ ] Configure CI/CD pipeline

### Phase 2: Core Registration (Week 2)

- [ ] Implement FastAPI REST endpoints
- [ ] Build authentication middleware (PAT validation)
- [ ] Create Pydantic models for `emerge.yaml`
- [ ] Implement validation service
- [ ] Build registration orchestration service
- [ ] Write unit tests (>80% coverage)

### Phase 3: Protocol Adapters (Week 3)

- [ ] Implement `BaseAdapter` abstract class
- [ ] Build MCP adapter
  - [ ] JSON-RPC 2.0 client
  - [ ] Parallel harvesting (tools/resources/prompts)
  - [ ] x402 metadata extraction
  - [ ] Retry logic with exponential backoff
- [ ] Build A2A adapter
  - [ ] Agent Card fetching
  - [ ] Per-capability security parsing
- [ ] Write adapter tests with mocked agents

### Phase 4: gRPC & Internal APIs (Week 4)

- [ ] Define protobuf messages
- [ ] Generate Python stubs
- [ ] Implement gRPC servicer
- [ ] Add health check endpoint
- [ ] Test gRPC calls from mock Planning service

### Phase 5: Background Services (Week 5)

- [ ] Implement health monitoring cron job
  - [ ] Parallel health checks (asyncio)
  - [ ] Update database via gRPC
- [ ] Implement version management
  - [ ] Snapshot creation on update
  - [ ] Conflict detection

### Phase 6: Observability (Week 6)

- [ ] Add Prometheus metrics
- [ ] Configure structured logging with `structlog`
- [ ] Setup OpenTelemetry tracing
- [ ] Create Grafana dashboards
- [ ] Configure Alertmanager rules
- [ ] Document runbooks for alerts

### Phase 7: Production Hardening (Week 7-8)

- [ ] Add rate limiting (per-user, per-endpoint)
- [ ] Implement request ID tracking
- [ ] Setup database connection pooling
- [ ] Configure backup strategy
- [ ] Write API documentation (Swagger/OpenAPI)
- [ ] Load testing (Locust/k6)
- [ ] Security audit (OWASP checklist)
- [ ] Deploy to staging environment

### Phase 8: Launch (Week 9)

- [ ] Final testing with real agent samples
- [ ] Documentation review
- [ ] Production deployment
- [ ] Monitor error rates
- [ ] Collect feedback from early users

---

## 11.5 Example emerge.yaml Configurations

### MCP Agent Example

```yaml
# File: examples/mcp-weather-agent.yaml

identity:
  id: "did:emerge:agent:weather-bot-01"
  name: "WeatherBot"
  version: "1.0.0"
  tags: ["weather", "forecast", "climate"]
  description: "Provides weather forecasts and climate data"

protocol:
  type: "mcp"
  version: "2025-11-25"  # Latest MCP protocol version
  transport:
    type: "sse"
    endpoint: "https://api.weatherbot.com/mcp/sse"

security:
  transport_layer:
    type: "tls"
  
  # MCP: Single session-level auth
  auth_strategies:
    - id: "strategy_api_key"
      type: "x_api_key"
      config:
        header_name: "X-WeatherBot-Key"
        key_vault_ref: "WEATHERBOT_API_KEY"

payment:
  type: "x402"
  config:
    enabled: true
    chain_id: "eip155:8453"
    recipient_address: "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    asset: "USDC"
    token_address: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    default_price: "10"
    currency: "USDC"
    # facilitator_url injected by registry

# What gets harvested automatically:
# - Tools via tools/list
# - Resources via resources/list
# - Prompts via prompts/list
# - x402 per-tool pricing from headers
```

### A2A Agent Example

```yaml
# File: examples/a2a-calendar-agent.yaml

identity:
  id: "did:emerge:agent:calendar-assistant-01"
  name: "CalendarAssistant"
  version: "2.0.0"
  tags: ["calendar", "scheduling", "productivity"]
  description: "Intelligent calendar management and meeting scheduling"

protocol:
  type: "a2a"
  version: "1.0"
  url: "https://api.calendar-agent.com"  # Base URL

# NO authSchemes here - harvested from Agent Card
# NO security section - harvested from /.well-known/agent.json

payment:
  type: "none"  # No payment required

# What gets harvested automatically:
# - Agent Card from GET /.well-known/agent.json
# - authSchemes[] array (applies to ALL skills)
# - skills[] array
# - Provider info, capabilities metadata
```

**What the Registry Will Harvest from A2A:**

From `GET https://api.calendar-agent.com/.well-known/agent.json`:

```json
{
  "schemaVersion": "1.0",
  "name": "CalendarAssistant",
  "description": "Intelligent calendar management",
  "url": "https://api.calendar-agent.com",
  
  "authSchemes": [
    {
      "scheme": "oauth2",
      "tokenUrl": "https://auth.calendar-agent.com/token",
      "scopes": ["calendar:read", "calendar:write"],
      "service_identifier": "calendar-oauth"
    },
    {
      "scheme": "apiKey",
      "description": "Alternative: API key for testing",
      "service_identifier": "calendar-api-key"
    }
  ],
  
  "skills": [
    {
      "id": "create_event",
      "name": "Create Event",
      "description": "Create a new calendar event",
      "input_schema": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "start_time": {"type": "string", "format": "date-time"},
          "duration_minutes": {"type": "integer"}
        },
        "required": ["title", "start_time"]
      }
    }
  ]
}
```

**Key Differences:**

| Aspect | MCP Agent | A2A Agent |
|--------|-----------|-----------|
| **Auth in emerge.yaml** | ✅ Required | ❌ Not provided |
| **Auth Source** | `emerge.yaml` security section | Harvested from Agent Card |
| **Auth Scope** | Session-level (transport) | Agent-level (all skills) |
| **Capabilities Source** | JSON-RPC calls | Static Agent Card |
| **Protocol Endpoint** | SSE/stdio/HTTP transport | Base HTTP URL |

---

**File:** `services/registry/.env.example`

```bash
# Database
DATABASE_URL=postgresql://emerge:password@localhost:5432/emerge_registry

# Server
HOST=0.0.0.0
PORT=8000
GRPC_PORT=50051

# Authentication
PAT_TOKEN_PREFIX=emerge_pat_

# Vault (optional)
VAULT_URL=
VAULT_TOKEN=

# Observability
LOG_LEVEL=info
JAEGER_HOST=localhost
JAEGER_PORT=6831

# Feature Flags
ENABLE_HEALTH_MONITORING=true
HEALTH_CHECK_INTERVAL_SECONDS=300

# Retry Configuration
MAX_HARVEST_RETRIES=3
HARVEST_TIMEOUT_SECONDS=10
```

---

## Appendix B: Example API Calls

### Register MCP Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -H "Authorization: Bearer emerge_pat_abc123..." \
  -F "emerge_yaml=@./examples/mcp-agent.yaml"
```

### Get Agent Manifest

```bash
curl http://localhost:8000/api/v1/agents/did:emerge:agent:my-agent-01 \
  -H "Authorization: Bearer emerge_pat_abc123..."
```

### List User's Agents

```bash
curl "http://localhost:8000/api/v1/agents?page=1&limit=10&status=healthy" \
  -H "Authorization: Bearer emerge_pat_abc123..."
```

---

## Appendix C: Prisma Commands Reference

```bash
# Development
uv run prisma migrate dev --name <name>       # Create + apply migration
uv run prisma studio                          # Open GUI

# Production
uv run prisma migrate deploy                  # Apply pending migrations
uv run prisma migrate status                  # Check migration status

# Debugging
uv run prisma db push                         # Sync without migration (dev only)
uv run prisma db pull                         # Introspect existing DB
uv run prisma format                          # Format schema.prisma

# Generation
uv run prisma generate                        # Generate Python client
```

---

## Appendix D: Testing Strategy

### Unit Tests

**File:** `services/registry/tests/test_mcp_adapter.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from adapters.mcp import MCPAdapter

@pytest.mark.asyncio
async def test_harvest_tools_success():
    """Test successful MCP tool harvesting."""
    adapter = MCPAdapter(endpoint="https://mock.agent.com")
    
    mock_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get weather data",
                    "inputSchema": {"type": "object"}
                }
            ]
        }
    }
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value.json.return_value = mock_response
        
        tools = await adapter._harvest_tools()
        
        assert len(tools) == 1
        assert tools[0].id == "get_weather"
        assert tools[0].type == "tool"

@pytest.mark.asyncio
async def test_harvest_retry_logic():
    """Test retry mechanism on failure."""
    adapter = MCPAdapter(endpoint="https://unreachable.com", max_retries=3)
    
    with patch('httpx.AsyncClient.post', side_effect=Exception("Connection error")):
        with pytest.raises(ConnectionError) as exc:
            await adapter.harvest()
        
        assert "Failed after 3 attempts" in str(exc.value)
```

### Integration Tests

**File:** `services/registry/tests/test_registration_flow.py`

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_full_registration_flow():
    """Test end-to-end registration."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Upload emerge.yaml
        files = {"emerge_yaml": open("tests/fixtures/mcp-agent.yaml", "rb")}
        headers = {"Authorization": "Bearer emerge_pat_test123456789"}
        
        response = await client.post(
            "/api/v1/agents/register",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "success"
        assert "agent_id" in data["data"]
```

---

## Appendix E: Further Reading

- **MCP Specification:** https://github.com/modelcontextprotocol/specification
- **A2A Protocol:** https://github.com/AgentProtocol/agent-protocol
- **Prisma Python Docs:** https://prisma-client-py.readthedocs.io/
- **FastAPI Best Practices:** https://fastapi.tiangolo.com/tutorial/
- **gRPC Python Guide:** https://grpc.io/docs/languages/python/
- **uv Documentation:** https://docs.astral.sh/uv/

---

**End of Document**

*This specification is a living document. Update as requirements evolve.*
