from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from handlers import handle_rpc

app = FastAPI()

@app.get("/healthz")
async def health():
    return {"ok": True, "service": "Proxy"}

@app.post("/rpc")
async def rpc(request: Request):
    body = await request.json()
    result = await handle_rpc(body)
    
    # Check if result has an error (JSON-RPC error format)
    if "error" in result:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "error": result["error"]
        })
    else:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": result
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
