# Test Manifest Server

A FastAPI-based test server for serving agent manifests during API testing and development.

## Running the Server

```bash
make test-manifest-server
```

The server will start on `http://localhost:9000`.

## Endpoints

### Read Endpoints

- `GET /` - Root endpoint showing available manifest types
- `GET /manifest?type=<type>` - Get agent manifest by type
- `GET /health` - Health check endpoint

### Write Endpoints

- `POST /upload` - Upload and register a new manifest
- `DELETE /manifests/<type>` - Delete a registered manifest

## Available Manifest Types

The server comes with pre-configured manifest types:

- **mcp** - Returns the MCP test manifest from `fixtures/mcp_emerge.yaml`
- **a2a** - Returns the A2A test manifest from `fixtures/a2a_emerge.yaml`

Any custom manifests uploaded via `/upload` will also be available.

## Usage in Tests

### Using Pre-loaded Manifests

Update your `emerge.yaml` files to point to the test server:

```yaml
protocol:
  transport:
    endpoint: "http://localhost:9000/manifest?type=mcp"

health_endpoint: "http://localhost:9000/health"
```

Then register the agent:

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -F "emerge_yaml=@services/registry/tests/fixtures/mcp_emerge.yaml"
```

### Uploading Custom Manifests

1. **Upload a custom manifest:**

```bash
curl -X POST http://localhost:9000/upload \
  -F "file=@my_custom_manifest.yaml" \
  -F "type=my_custom_agent"
```

Response:
```json
{
  "status": "success",
  "type": "my_custom_agent",
  "manifest_name": "MyCustomAgent",
  "file_path": "/path/to/fixtures/my_custom_agent_emerge.yaml",
  "endpoint": "/manifest?type=my_custom_agent",
  "message": "Manifest type 'my_custom_agent' registered and ready to serve"
}
```

2. **Reference it in your test manifest:**

```yaml
identity:
  id: "did:metaorcha:agent:my-agent"
  name: "MyAgent"
  version: "1.0.0"

protocol:
  transport:
    endpoint: "http://localhost:9000/manifest?type=my_custom_agent"

health_endpoint: "http://localhost:9000/health"
```

3. **Register the agent:**

```bash
curl -X POST http://localhost:8000/api/v1/agents/register \
  -F "emerge_yaml=@my_agent_manifest.yaml"
```

### Complete Testing Workflow with Custom Manifest

```bash
# 1. Start the test manifest server
make test-manifest-server &

# 2. Start the registry service
make dev s=registry &

# 3. Upload a custom manifest to the test server
curl -X POST http://localhost:9000/upload \
  -F "file=@my_custom_manifest.yaml" \
  -F "type=my_custom_agent"

# 4. Create your agent manifest that references the custom manifest
cat > my_agent.yaml << 'EOF'
identity:
  id: "did:metaorcha:agent:test"
  name: "TestAgent"
  version: "1.0.0"
  description: "Test agent"
  tags: ["test"]

protocol:
  type: "mcp"
  version: "2025-11-25"
  transport:
    type: "sse"
    endpoint: "http://localhost:9000/manifest?type=my_custom_agent"

health_endpoint: "http://localhost:9000/health"

security:
  transport_layer:
    type: "none"
  auth_strategies: []

payment:
  type: "none"
EOF

# 5. Register the agent with the registry
curl -X POST http://localhost:8000/api/v1/agents/register \
  -F "emerge_yaml=@my_agent.yaml"

# 6. Verify the agent was registered
curl http://localhost:8000/api/v1/agents

# 7. Cleanup
make test-manifest-server-stop
```

## Architecture: ManifestProvider Pattern

The server uses the **Provider Pattern** for extensibility:

### Base Class: `ManifestProvider`

```python
class ManifestProvider:
    def get_type(self) -> str:
        """Return the manifest type this provider handles."""
        raise NotImplementedError

    async def get_manifest(self) -> Dict[str, Any]:
        """Return the manifest as a dict."""
        raise NotImplementedError
```

### Concrete Implementation: `FileManifestProvider`

```python
provider = FileManifestProvider("mcp", Path("fixtures/mcp_emerge.yaml"))
registry.register(provider)
```

### Registry: `ManifestRegistry`

```python
registry = ManifestRegistry()
registry.register(mcp_provider)
manifest = await registry.get_manifest("mcp")
```

## Adding Custom Manifests

### Option 1: Add a New File-Based Manifest

1. Create a new YAML file in `fixtures/`:

```bash
cat > services/registry/tests/fixtures/custom_emerge.yaml << 'EOF'
identity:
  id: "did:metaorcha:agent:custom"
  name: "CustomAgent"
  version: "1.0.0"
  description: "A custom test agent"
  tags: ["custom"]

protocol:
  type: "mcp"
  version: "2025-11-25"
  transport:
    type: "sse"
    endpoint: "http://localhost:9000/manifest?type=custom"

health_endpoint: "http://localhost:9000/health"

security:
  transport_layer:
    type: "none"
  auth_strategies: []

payment:
  type: "none"
EOF
```

2. The provider will automatically be registered on server startup.

### Option 2: Create a Custom Provider

For dynamic or programmatic manifests, create a custom provider:

```python
class DynamicManifestProvider(ManifestProvider):
    """Provider that generates manifests dynamically."""

    def get_type(self) -> str:
        return "dynamic"

    async def get_manifest(self) -> Dict[str, Any]:
        return {
            "identity": {
                "id": f"did:metaorcha:agent:dynamic-{uuid4()}",
                "name": "DynamicAgent",
                "version": "1.0.0",
                # ... rest of manifest
            }
        }

# In manifest_server.py startup:
registry.register(DynamicManifestProvider())
```

### Option 3: Database-Backed Provider

```python
class DatabaseManifestProvider(ManifestProvider):
    """Provider that loads manifests from database."""

    def __init__(self, db, manifest_id: str):
        self.db = db
        self.manifest_id = manifest_id

    def get_type(self) -> str:
        return f"db:{self.manifest_id}"

    async def get_manifest(self) -> Dict[str, Any]:
        manifest = await self.db.manifest.find_unique(
            where={"id": self.manifest_id}
        )
        return manifest.data if manifest else {}
```

## Testing Workflow

1. **Start the test server:**
   ```bash
   make test-manifest-server &
   ```

2. **In another terminal, start the registry service:**
   ```bash
   make dev s=registry
   ```

3. **Register an agent:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/agents/register \
     -F "emerge_yaml=@services/registry/tests/fixtures/mcp_emerge.yaml"
   ```

4. **Stop the test server when done:**
   ```bash
   make test-manifest-server-stop
   ```

## Upload Validation

The `/upload` endpoint validates:

- **YAML syntax**: File must be valid YAML
- **Type identifier**: Must be alphanumeric with optional hyphens/underscores
- **Uniqueness**: Type must not already exist in the registry
- **Manifest structure**: Must be a YAML object (dict), not a scalar/list

### Example Validation Errors

**Invalid YAML:**
```bash
curl -X POST http://localhost:9000/upload \
  -F "file=@invalid.yaml" \
  -F "type=test"
```

Response (400):
```json
{
  "detail": {
    "error": "Invalid YAML: mapping values are not allowed here"
  }
}
```

**Duplicate type:**
```bash
curl -X POST http://localhost:9000/upload \
  -F "file=@manifest.yaml" \
  -F "type=mcp"
```

Response (409):
```json
{
  "detail": {
    "error": "Manifest type 'mcp' already registered",
    "existing_types": ["mcp", "a2a"]
  }
}
```

**Invalid type identifier:**
```bash
curl -X POST http://localhost:9000/upload \
  -F "file=@manifest.yaml" \
  -F "type=invalid@type!"
```

Response (400):
```json
{
  "detail": {
    "error": "Invalid manifest type. Must be alphanumeric (hyphens and underscores allowed)"
  }
}
```

## Deleting Manifests

Delete custom manifests (but not the default mcp/a2a types):

```bash
curl -X DELETE http://localhost:9000/manifests/my_custom_agent
```

Response:
```json
{
  "status": "success",
  "type": "my_custom_agent",
  "message": "Manifest type 'my_custom_agent' deleted"
}
```

## Design Benefits

- **Extensible**: Add new manifest types without modifying the HTTP endpoint
- **Testable**: Easy to mock or create test implementations
- **Pluggable**: Providers can be added/removed at runtime
- **Maintainable**: Clear separation of concerns
- **Flexible**: Supports file-based, database-backed, or dynamically generated manifests
- **Developer-friendly**: Upload custom manifests on-the-fly for testing
