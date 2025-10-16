# Orcha-2 Quick Start

## 1. Start the Backend Server
```powershell
.\scripts\start-server.ps1
```

## 2. Test All Endpoints  
```powershell
.\scripts\test-endpoints.ps1
```

## 3. Open the UI
```powershell
.\scripts\open-ui.ps1
```

## 4. Full Integration Test
```powershell
.\scripts\test-full.ps1
```

---

## What's Included

- **orcha-2/**: Complete automation backend with Phase 5 features
- **RP2A/**: Restaurant integration components  
- **.env**: Environment configuration
- **scripts/**: Simple PowerShell scripts for testing

## Architecture Overview

```
Browser UI (chat.html) 
    ↓ HTTP
Orcha-2 FastAPI Server (port 8000)
    ↓ Session Management  
LLM Client (Ollama + OpenAI fallback)
    ↓ Intent Classification
Menu Provider (BM25 Search)
    ↓ Structured Results
```


