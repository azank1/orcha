[Client (e.g., MCP Client)] 
    ↓ (JSON-RPC)
[MCP Server (9090)] ──→ [Proxy (8080)] ──→ [P2A (8000)] ──→ [Vendor API (e.g., FoodTec)]
    ↑                    ↑                   ↑
    │                    │                   │
    └── Tools:           └── Policy:         └── Adapters:
        foodtec.*         Idempotency,        Mock or Real
        Discovery         Logging,            (switch via P2A_VENDOR)
        Health            Caching