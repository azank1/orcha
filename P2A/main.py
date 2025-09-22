import contextlib
import os
import time
import uuid
from typing import Any, Dict
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from starlette.requests import Request
from dotenv import load_dotenv
from vendor_select import get_services
from core.mcp.menu_mcp import mcp as menu_mcp
from core.mcp.order_mcp import mcp as order_mcp
import logging

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Application configuration
APP_NAME = "P2A MCP"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "POS Agent Adapter MCP Server"


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(menu_mcp.session_manager.run())
        await stack.enter_async_context(order_mcp.session_manager.run())
        yield


async def healthz(request):
    return JSONResponse({"ok": True, "service": APP_NAME, "version": APP_VERSION})

# --- Simple JSON-RPC endpoint with idempotent order.accept ---
IDEMPOTENCY_TTL_MS = 600_000  # 10 minutes
_accept_ledger: Dict[str, Dict[str, Any]] = {}


def _rpc_ok(_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": _id, "result": result}


def _rpc_err(_id: Any, code: int, message: str, data: Any | None = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": _id, "error": err}


async def rpc(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(_rpc_err(None, -32700, "Parse error"), status_code=400)

    # Support only single-call objects for this lightweight mock
    if not isinstance(body, dict) or body.get("jsonrpc") != "2.0":
        return JSONResponse(_rpc_err(body.get("id") if isinstance(body, dict) else None, -32600, "Invalid Request"), status_code=400)

    _id = body.get("id")
    method = body.get("method")
    params = body.get("params") or {}

    # FoodTec contract methods bridged via P2A services
    if method == "foodtec.export_menu":
        vendor = os.getenv("P2A_VENDOR", "mock")
        menu_service, _ = get_services(vendor)
        store_id = (params or {}).get("store_id") or "default"
        # Default paging in mock mode
        page = (params or {}).get("page") or 1
        page_size = (params or {}).get("page_size") or 50
        q = (params or {}).get("q")
        try:
            if hasattr(menu_service, "export_menu"):
                maybe = menu_service.export_menu(store_id=store_id, page=page, page_size=page_size, q=q)
                if hasattr(maybe, "__await__"):
                    result = await maybe
                else:
                    result = maybe
            else:
                # Fallback: build export shape from mock menu service
                from menu_service_mock_export import MenuServiceExportMock
                result = await MenuServiceExportMock().export_menu(store_id=store_id, page=page, page_size=page_size, q=q)
            return JSONResponse(_rpc_ok(_id, result))
        except Exception as exc:
            return JSONResponse(_rpc_err(_id, -32000, "EXPORT_FAILED", {"message": str(exc)}), status_code=500)

    if method == "foodtec.validate_order":
        vendor = os.getenv("P2A_VENDOR", "mock")
        _, order_service = get_services(vendor)
        if order_service is None:
            return JSONResponse(_rpc_err(_id, -32601, "Method not available for mock vendor"), status_code=404)
        payload = params or {}
        result = order_service.validate_order(payload)
        # map error status to HTTP 422 when ok:false and upstream indicates validation
        if not result.get("ok", False):
            return JSONResponse(_rpc_err(_id, -32000, result.get("message", "Validation failed"), result), status_code=422)
        return JSONResponse(_rpc_ok(_id, result))

    if method == "foodtec.accept_order":
        vendor = os.getenv("P2A_VENDOR", "mock")
        _, order_service = get_services(vendor)
        if order_service is None:
            return JSONResponse(_rpc_err(_id, -32601, "Method not available for mock vendor"), status_code=404)
        idem = (params or {}).get("idem") or request.headers.get("Idempotency-Key") or uuid.uuid4().hex
        payload = (params or {}).get("draft") or params or {}
        result = order_service.accept_order(payload, idem=idem)
        if not result.get("ok", False):
            return JSONResponse(_rpc_err(_id, -32000, result.get("message", "Accept failed"), result), status_code=400)
        # honor idempotency echo in response; header is optional at this layer (Engine validates headers deeply)
        return JSONResponse(_rpc_ok(_id, result), headers={"Idempotency-Key": idem})

    # Fallback to mock idempotent accept used for local testing
    if method != "order.accept":
        return JSONResponse(_rpc_err(_id, -32601, f"Method not found: {method}"), status_code=404)

    # Idempotency handling via header
    idem = request.headers.get("Idempotency-Key")
    if not idem:
        return JSONResponse(_rpc_err(_id, -32000, "Idempotency-Key header is required"), status_code=400)

    now = int(time.time() * 1000)
    entry = _accept_ledger.get(idem)
    if entry and (now - entry["t"] < IDEMPOTENCY_TTL_MS):
        # Replay: return cached response with replay header
        headers = {"X-Idempotency-Replay": "true", "Idempotency-Key": idem}
        return JSONResponse(entry["response"], headers=headers)

    # Basic validation (very light for mock)
    draft = params.get("draft") or {}
    items = draft.get("items") if isinstance(draft, dict) else None
    if not isinstance(items, list) or not items:
        return JSONResponse(_rpc_err(_id, -32000, "VALIDATION_ERROR", {"message": "No items provided"}), status_code=422)

    # Create confirmation and cache it
    confirmation = _rpc_ok(
        _id,
        {
            "ok": True,
            "order_id": f"P2A-{now}-{uuid.uuid4().hex[:6]}",
            "idem": idem,
        },
    )

    _accept_ledger[idem] = {"t": now, "response": confirmation}

    return JSONResponse(confirmation, headers={"Idempotency-Key": idem})

app = Starlette(
    routes=[
        Route("/healthz", healthz),
        Route("/rpc", rpc, methods=["POST"]),
        Mount("/menu", app=menu_mcp.streamable_http_app()),
        Mount("/order", app=order_mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)

if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run("main:app", host=host, port=port, reload=debug, log_level="info")
