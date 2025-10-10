# Orcha-2 Automation Layer

## How to Run the Automation API

From the `orcha-2` directory, start the FastAPI service:

```powershell
cd d:\dev\orcha-1\orcha-2
uvicorn automation.main:app --host 127.0.0.1 --port 5000 --reload
```

Tip: When testing WebSockets in a separate terminal, you can disable reload to avoid service restarts mid-session:

```powershell
uvicorn automation.main:app --host 127.0.0.1 --port 5000
```

## API Endpoints
- `GET /automation/search?query=pizza` — Search menu items
- `GET /health` — Service health check
- `WS /automation/ws` — WebSocket orchestrator (send `{ "text": "...", "session_id": "..." }`)

## LLM Provider Configuration
The orchestrator supports multiple providers for intent parsing:

Provider selection order if `LLM_PROVIDER` is not set:
1. Ollama (if `OLLAMA_HOST` is set)
2. Hugging Face (if `HF_API_KEY` is set)
3. OpenAI (if `OPENAI_API_KEY` is set)
4. Stub (fallback)

You can explicitly select a provider:

```powershell
$env:LLM_PROVIDER = "ollama"    # or "huggingface", "openai", "stub"
```

### Ollama (local)
1. Install: https://ollama.com
2. Pull a model (example):
	```powershell
	ollama pull llama3.1:8b
	```
3. Set environment (PowerShell):
	```powershell
	$env:LLM_PROVIDER = "ollama"
	$env:OLLAMA_HOST = "http://127.0.0.1:11434"
	$env:OLLAMA_MODEL = "llama3.1:8b"
	```

### Hugging Face Inference API
1. Get an API token: https://huggingface.co/settings/tokens
2. Choose a chat/instruct model (examples):
	- `mistralai/Mistral-7B-Instruct-v0.2`
	- `HuggingFaceH4/zephyr-7b-beta`
3. Set environment:
	```powershell
	$env:LLM_PROVIDER = "huggingface"
	$env:HF_API_KEY = "<your_hf_token>"
	$env:HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
	```

### OpenAI (optional)
```powershell
$env:LLM_PROVIDER = "openai"
$env:OPENAI_API_KEY = "<your_openai_key>"
$env:OPENAI_MODEL = "gpt-3.5-turbo"
```

If a provider fails (e.g., rate limit), the system falls back to a local stub so sessions remain stable.

## Test WebSocket Orchestrator
With the server running:

```powershell
python automation\tests\test_ws_client.py
```

Expected outputs include a search response, order response, and an unknown intent fallback.
