# Orcha-1 Automation

LLM-powered automation for the Orcha-1 FoodTec integration, enabling natural language processing of food orders.

## Directory Structure

```
automation/
├── requirements.txt        # Python deps
├── README.md               # Docs for automation module
├── main.py                 # Entry point for orchestration server/CLI
├── orchestrator/           # Core orchestration logic
│   ├── __init__.py
│   ├── llm.py              # LLM wrapper (LangChain/OpenAI)
│   ├── planner.py          # Plans steps: export → validate → accept
│   ├── runner.py           # Executes plan against MCP
│   └── schemas.py          # Shared schemas for payloads
├── clients/                # MCP/Proxy clients
│   ├── __init__.py
│   ├── mcp_client.py       # JSON-RPC client for MCP (9090)
│   └── proxy_client.py     # JSON-RPC client for Proxy (8080)
└── tests/
    ├── test_llm.py
    ├── test_runner.py
    └── test_e2e.py
```

## Setup

1. Install dependencies:

```bash
cd automation
pip install -r requirements.txt
```

2. Set OpenAI API Key:

```bash
# Linux/Mac
export OPENAI_API_KEY=your-key-here

# Windows PowerShell
$env:OPENAI_API_KEY="your-key-here"
```

## Usage

### Starting the Automation CLI

Make sure your Orcha-1 stack is running:

1. Start Proxy: `cd proxy && python main.py` (or `uvicorn proxy.main:app --reload --port 8080`)
2. Start MCP: `cd MCP && node dist/index.js`
3. Start Automation CLI: `cd automation && python main.py`

### Using the CLI

Once the CLI is running, you can interact with it:

```
🤖 Orcha-1 Automation CLI
Type 'exit' or 'quit' to end the session

👤 You: show me the menu
📦 Planner chose tool: foodtec.export_menu
MCP Response: { ... menu data ... }

👤 You: place an order
📦 Planner chose tool: foodtec.validate_order
MCP Response: { ... validation response ... }

👤 You: confirm my order
📦 Planner chose tool: foodtec.accept_order
MCP Response: { ... acceptance response ... }
```

## Testing

### Unit Tests

```bash
pytest tests/test_llm.py tests/test_runner.py
```

### End-to-End Tests

To run E2E tests that interact with the actual MCP server:

```bash
# Enable E2E tests
export RUN_E2E_TESTS=1

# Run the tests
pytest tests/test_e2e.py
```

## LLM Integration

This module uses LangChain with OpenAI's models to process natural language orders. The LLMWrapper class encapsulates the language model interactions, making it easy to switch between different models or providers.

### Planner Logic

The planner uses LLM to determine which action to take:

1. For menu requests → `foodtec.export_menu`
2. For order confirmation → `foodtec.validate_order`
3. For final orders → `foodtec.accept_order`

The prompt structure ensures consistent decision-making based on user intent.

## Integration with MCP UI

The Automation component can be integrated with the MCP UI by:

1. Creating a simple REST API using FastAPI or Flask
2. Adding endpoints for the UI to call
3. Implementing WebSocket support for real-time updates

Details on this integration can be found in `docs/ui_automation_integration.md`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
