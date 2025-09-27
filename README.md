# Orcha-1

MCP → Proxy → API

## Install
```
cd MCP && npm install && npm run build
cd P2A && pip install -r requirements.txt  
cd proxy && pip install -r requirements.txt
```

## Start Servers
```
cd proxy && python main.py
```
```
cd MCP && node dist/index.js
```

## Test Entire Loop
```
cd tests && .\run_all.ps1
```
