"""
Ecommerce Automation Agent — A2A-compatible server.

Exposes:
- POST /                       → A2A JSON-RPC 2.0 endpoint (message/send, tasks/get)
- GET  /.well-known/agent.json → Agent Card
- POST /a2a/tasks/send         → receives NL tasks, returns results (legacy)
- GET  /health                 → health check + credential status

Skills:
- shopify_management: Create, list, publish, unpublish, and delete Shopify products.
- social_publishing:  Publish posts and images to Facebook / Instagram.
- store_analytics:    Fetch Instagram insights and Facebook engagement metrics.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from contextvars import ContextVar
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from .config import settings
from .oauth_routes import router as oauth_router
from .token_store import get_token
from .tools import facebook, instagram, shopify

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

# ── ContextVars for per-request credential injection ──────────────────────────
shopify_access_token: ContextVar[str | None] = ContextVar("shopify_access_token", default=None)
shopify_store_url: ContextVar[str | None] = ContextVar("shopify_store_url", default=None)

app = FastAPI(title="Ecommerce Automation Agent (A2A)", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class OAuthHeaderMiddleware:
    """ASGI middleware that captures Authorization bearer tokens and extra
    headers into contextvars for per-request credential injection."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            auth = headers.get(b"authorization", b"").decode()
            store_url = headers.get(b"x-shopify-store-url", b"").decode()

            tok_token = shopify_access_token.set(auth[7:] if auth.lower().startswith("bearer ") else None)
            tok_store = shopify_store_url.set(store_url or None)
            try:
                await self.app(scope, receive, send)
            finally:
                shopify_access_token.reset(tok_token)
                shopify_store_url.reset(tok_store)
            return
        await self.app(scope, receive, send)


app.add_middleware(OAuthHeaderMiddleware)


class _TimingMiddleware(BaseHTTPMiddleware):
    """Emit a structured log event for every request: method, path, status, duration_ms."""

    async def dispatch(self, request, call_next):
        t0 = time.perf_counter()
        response = await call_next(request)
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round((time.perf_counter() - t0) * 1000, 1),
        )
        return response


app.add_middleware(_TimingMiddleware)
app.include_router(oauth_router)


# ── Agent Card ────────────────────────────────────────────────────────────────

AGENT_CARD = {
    "name": "Ecommerce Automation",
    "description": (
        "E-commerce automation agent covering Shopify product management, "
        "Facebook/Instagram social publishing, and social engagement analytics. "
        "Send a natural language task describing what to do."
    ),
    "url": f"http://localhost:{os.getenv('PORT', '3009')}",
    "version": "0.1.0",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "skills": [
        {
            "id": "shopify_management",
            "name": "Shopify Management",
            "description": (
                "Full CRUD for Shopify products via the Shopify Admin REST API: create, list "
                "(optionally filtered by active/draft status), get one, update (title, price, "
                "description, SKU, vendor, tags), publish, unpublish, delete one, and bulk-delete "
                "by status. IMPORTANT: When creating a product, you MUST include all details "
                "(title, price, description, SKU, vendor, tags) in the initial create request. "
                "Do NOT split creation and updating into multiple steps."
            ),
            "tags": ["shopify", "product", "listing", "inventory", "ecommerce", "crud", "bulk"],
            "examples": [
                "Create a Shopify product called 'Air Max 90' priced at $149.99 SKU AM-90 vendor Nike",
                "List all active products",
                "List all draft products",
                "Update Metanova Earbuds: set price to $199.99 and SKU to META-001",
                "Publish product ID 1234567890",
                "Delete product 9876543210",
                "Delete all draft products",
            ],
        },
        {
            "id": "social_publishing",
            "name": "Social Publishing",
            "description": (
                "Publish text posts and images to a Facebook Page and to an Instagram "
                "Business account. Also supports deleting posts and replying to comments."
            ),
            "tags": ["facebook", "instagram", "post", "publish", "social", "caption", "image"],
            "examples": [
                "Post 'New arrivals just dropped!' to our Facebook Page",
                "Publish this product image to Instagram with caption 'Fresh drop'",
                "Reply 'Thanks for the love! ❤️' to comment 123456789",
            ],
        },
        {
            "id": "store_analytics",
            "name": "Store Analytics",
            "description": (
                "Retrieve engagement analytics: Instagram media insights (impressions, reach, "
                "likes, saves) and Facebook post likes/comment counts."
            ),
            "tags": ["analytics", "insights", "likes", "comments", "engagement", "reach", "impressions"],
            "examples": [
                "How many likes does post 123456 have?",
                "Get Instagram insights for media post 98765",
                "How many comments does our last Facebook post have?",
            ],
        },
    ],
}


@app.get("/.well-known/agent.json")
async def get_agent_card():
    return AGENT_CARD


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "agent": "ecommerce-automation",
        "version": "0.1.0",
        "shopify_configured": bool(settings.shopify_store_url and settings.shopify_access_token),
        "facebook_configured": bool(settings.fb_access_token and settings.fb_page_id),
        "instagram_configured": bool(settings.ig_access_token and settings.ig_user_id),
    }


# ── In-memory task store (for JSON-RPC tasks/get polling) ─────────────────────

_task_store: dict[str, dict[str, Any]] = {}


# ── A2A JSON-RPC 2.0 root endpoint ───────────────────────────────────────────


@app.post("/")
async def jsonrpc_endpoint(body: dict[str, Any]):
    """A2A JSON-RPC 2.0 dispatcher — handles message/send and tasks/get."""
    rpc_id = body.get("id", "")
    method = body.get("method", "")
    params = body.get("params", {})

    if method == "message/send":
        message = params.get("message", {})
        task_id = params.get("taskId") or message.get("taskId") or str(uuid.uuid4())

        # Extract text from parts (support both "kind" and "type" keys)
        parts = message.get("parts", [])
        text_parts = [
            p.get("text", "")
            for p in parts
            if p.get("kind") == "text" or p.get("type") == "text"
        ]
        query = " ".join(text_parts).strip()

        logger.info("jsonrpc_task_received", task_id=task_id, method=method, query=query[:200])

        task_result = await _execute_task(task_id, query, params=params)
        _task_store[task_id] = task_result

        return {"jsonrpc": "2.0", "id": rpc_id, "result": task_result}

    elif method == "tasks/get":
        task_id = params.get("id", "")
        task = _task_store.get(task_id)
        if task is None:
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32602, "message": f"Task {task_id!r} not found"},
            }
        return {"jsonrpc": "2.0", "id": rpc_id, "result": task}

    else:
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32601, "message": f"Method not found: {method!r}"},
        }


def _session_key_from_params(params: dict[str, Any] | None) -> str:
    if not isinstance(params, dict):
        return ""
    meta = params.get("metadata") or {}
    if not isinstance(meta, dict):
        return ""
    return str(meta.get("session_id") or meta.get("oauth_state") or "")


def _has_shopify_auth(session_key: str) -> bool:
    if shopify_access_token.get():
        return True
    if settings.shopify_access_token:
        return True
    if not session_key:
        return False
    return get_token(session_key) is not None


def _task_auth_required(task_id: str) -> dict[str, Any]:
    return {
        "id": task_id,
        "status": {
            "state": "auth-required",
            "message": {
                "role": "agent",
                "parts": [
                    {
                        "kind": "text",
                        "text": (
                            "Shopify authentication is required. "
                            "Please complete the OAuth flow to grant access."
                        ),
                    }
                ],
            },
        },
        "metadata": {"interrupt_type": "auth"},
    }


async def _execute_task(
    task_id: str,
    query: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a task and return the A2A task result object."""
    if not query:
        return _task_failed(task_id, "No text message provided")

    skill = _detect_skill(query)
    session_key = _session_key_from_params(params)

    try:
        if skill == "shopify_management":
            if not _has_shopify_auth(session_key):
                logger.info("shopify_auth_required task_id=%s", task_id)
                return _task_auth_required(task_id)

            tok_token = None
            tok_store = None
            if not shopify_access_token.get() and session_key:
                stored = get_token(session_key)
                if stored:
                    tok_token = shopify_access_token.set(stored.access_token)
                    if settings.shopify_store_url and not shopify_store_url.get():
                        tok_store = shopify_store_url.set(settings.shopify_store_url)

            try:
                result = await _handle_shopify(query)
            finally:
                if tok_token is not None:
                    shopify_access_token.reset(tok_token)
                if tok_store is not None:
                    shopify_store_url.reset(tok_store)
        elif skill == "social_publishing":
            result = await _handle_social_publishing(query)
        else:
            result = await _handle_store_analytics(query)

        answer = json.dumps(result, indent=2) if isinstance(result, dict) else str(result)

        return {
            "id": task_id,
            "status": {
                "state": "completed",
                "message": {
                    "role": "agent",
                    "parts": [{"type": "text", "text": answer}],
                },
            },
            "artifacts": [{"parts": [{"type": "text", "text": answer}]}],
        }

    except Exception as exc:
        logger.error("task_failed", task_id=task_id, error=str(exc))
        return _task_failed(task_id, str(exc))


# ── Legacy REST endpoint ──────────────────────────────────────────────────────


@app.post("/a2a/tasks/send")
async def send_task(body: dict[str, Any]):
    """Legacy A2A REST endpoint — delegates to _execute_task."""
    task_id = body.get("id", f"task_{uuid.uuid4().hex[:12]}")

    message = body.get("message", {})
    parts = message.get("parts", [])
    text_parts = [p["text"] for p in parts if p.get("type") == "text"]
    query = " ".join(text_parts).strip()

    logger.info("legacy_task_received", task_id=task_id, query=query[:200])
    return await _execute_task(
        task_id,
        query,
        params={"metadata": body.get("metadata") or {}},
    )


# ── Skill handlers ────────────────────────────────────────────────────────────


async def _handle_shopify(query: str) -> dict[str, Any]:
    """Route Shopify queries to the right CRUD operation."""
    q = query.lower()

    if any(w in q for w in ["create", "add", "new product", "make a product"]):
        params = _parse_product_params(query)
        result = await shopify.create_product(**params)
        return {"skill": "shopify_management", "action": "create_product", **result}

    if any(w in q for w in ["update", "change", "modify", "set price", "rename", "edit"]):
        product_id = _extract_id(query) or await _resolve_product_id_by_name(query)
        if not product_id:
            return {"skill": "shopify_management", "action": "update_product", "status": "error", "error": "Could not find a product matching that name. Try listing products first."}
        params = _parse_product_params(query)
        result = await shopify.update_product(
            product_id,
            price=params.get("price", "") if params.get("price") != "0.00" else "",
            title=params.get("title", "") if params.get("title") != "New Product" else "",
            description=params.get("description", ""),
            sku=params.get("sku", ""),
            vendor=params.get("vendor", ""),
            tags=params.get("tags", ""),
        )
        return {"skill": "shopify_management", "action": "update_product", **result}

    if any(w in q for w in ["unpublish", "deactivate", "hide"]) or (
        "draft" in q and any(w in q for w in ["set", "make", "move", "change"])
    ):
        product_id = _extract_id(query) or await _resolve_product_id_by_name(query)
        if not product_id:
            return {"skill": "shopify_management", "action": "unpublish_product", "status": "error", "error": "Could not find a product matching that name. Try listing products first."}
        result = await shopify.unpublish_product(product_id)
        return {"skill": "shopify_management", "action": "unpublish_product", **result}

    if any(w in q for w in ["publish", "activate", "go live"]):
        product_id = _extract_id(query) or await _resolve_product_id_by_name(query)
        if not product_id:
            return {"skill": "shopify_management", "action": "publish_product", "status": "error", "error": "Could not find a product matching that name. Try listing products first."}
        result = await shopify.publish_product(product_id)
        return {"skill": "shopify_management", "action": "publish_product", **result}

    # Bulk delete must come BEFORE single-delete branch
    if any(p in q for p in ["delete all", "remove all", "bulk delete", "clear all", "wipe"]):
        status_filter = ""
        if "draft" in q:
            status_filter = "draft"
        elif any(w in q for w in ["active", "published", "live"]):
            status_filter = "active"
        listing = await shopify.get_products(limit=250, status=status_filter)
        products = listing.get("products", [])
        deleted: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []
        for p in products:
            pid = str(p.get("id", ""))
            res = await shopify.delete_product(pid)
            if res.get("status") == "ok":
                deleted.append({"id": pid, "title": p.get("title", "")})
            else:
                failed.append({"id": pid, "title": p.get("title", ""), "error": res.get("error", "")})
        return {
            "skill": "shopify_management",
            "action": "bulk_delete_products",
            "status": "ok" if not failed else "partial",
            "filter": status_filter or "all",
            "deleted_count": len(deleted),
            "failed_count": len(failed),
            "deleted": deleted,
            "failed": failed,
        }

    if any(w in q for w in ["delete", "remove", "destroy"]):
        product_id = _extract_id(query) or await _resolve_product_id_by_name(query)
        if not product_id:
            return {"skill": "shopify_management", "action": "delete_product", "status": "error", "error": "Could not find a product matching that name. Try listing products first."}
        result = await shopify.delete_product(product_id)
        return {"skill": "shopify_management", "action": "delete_product", **result}

    if any(w in q for w in ["get product", "fetch product", "find product"]):
        product_id = _extract_id(query) or await _resolve_product_id_by_name(query)
        if not product_id:
            return {"skill": "shopify_management", "action": "get_product", "status": "error", "error": "Could not find a product matching that name. Try listing products first."}
        result = await shopify.get_product_by_id(product_id)
        return {"skill": "shopify_management", "action": "get_product", **result}

    # List with optional status filter — "list active", "list draft", "show published"
    status_filter = ""
    if any(w in q for w in ["active", "published", "live"]):
        status_filter = "active"
    elif "draft" in q or "unpublished" in q:
        status_filter = "draft"
    result = await shopify.get_products(limit=10, status=status_filter)
    action = f"get_products_{status_filter}" if status_filter else "get_products"
    return {"skill": "shopify_management", "action": action, **result}


async def _handle_social_publishing(query: str) -> dict[str, Any]:
    """Route social publishing queries."""
    q = query.lower()

    # Instagram publish
    if any(w in q for w in ["instagram", "ig", "insta"]):
        if any(w in q for w in ["publish", "post", "share", "upload"]):
            image_url, caption = _parse_publish_params(query)
            result = await instagram.publish_media(image_url=image_url, caption=caption)
            return {"skill": "social_publishing", "platform": "instagram", "action": "publish_media", **result}
        # Default IG action: get recent posts
        result = await instagram.get_media_posts(limit=5)
        return {"skill": "social_publishing", "platform": "instagram", "action": "get_media_posts", **result}

    # Facebook delete
    if any(w in q for w in ["delete post", "remove post"]):
        post_id = _extract_id(query)
        result = await facebook.delete_post(post_id)
        return {"skill": "social_publishing", "platform": "facebook", "action": "delete_post", **result}

    # Facebook image
    if any(w in q for w in ["image", "photo", "picture"]):
        image_url, caption = _parse_publish_params(query)
        result = await facebook.post_image(image_url=image_url, caption=caption)
        return {"skill": "social_publishing", "platform": "facebook", "action": "post_image", **result}

    # Facebook reply to comment
    if any(w in q for w in ["reply", "reply to comment"]):
        comment_id = _extract_id(query)
        message = _extract_quoted_text(query) or query
        result = await facebook.reply_to_comment(comment_id=comment_id, message=message)
        return {"skill": "social_publishing", "platform": "facebook", "action": "reply_to_comment", **result}

    # Default: Facebook text post
    message = _extract_quoted_text(query) or query
    result = await facebook.create_post(message=message)
    return {"skill": "social_publishing", "platform": "facebook", "action": "create_post", **result}


async def _handle_store_analytics(query: str) -> dict[str, Any]:
    """Route analytics queries."""
    q = query.lower()
    post_id = _extract_id(query)

    if any(w in q for w in ["instagram", "ig", "insta", "media insight", "impression", "reach", "saved"]):
        result = await instagram.get_media_insights(media_id=post_id or "mock_media_1")
        return {"skill": "store_analytics", "platform": "instagram", "action": "get_media_insights", **result}

    if any(w in q for w in ["like", "likes"]):
        result = await facebook.get_number_of_likes(post_id=post_id or "mock_post_1")
        return {"skill": "store_analytics", "platform": "facebook", "action": "get_number_of_likes", **result}

    if any(w in q for w in ["comment", "comments"]):
        result = await facebook.get_number_of_comments(post_id=post_id or "mock_post_1")
        return {"skill": "store_analytics", "platform": "facebook", "action": "get_number_of_comments", **result}

    # Default: Facebook page posts list
    result = await facebook.get_page_posts(limit=5)
    return {"skill": "store_analytics", "platform": "facebook", "action": "get_page_posts", **result}


# ── Intent detection ──────────────────────────────────────────────────────────


def _detect_skill(query: str) -> str:
    """Keyword-based skill routing."""
    q = query.lower()

    shopify_signals = [
        "shopify", "product", "listing", "inventory", "sku",
        "create product", "add product", "publish product",
        "unpublish", "store product",
        "delete all", "bulk delete", "wipe products", "clear all products",
        "list active", "list draft", "list published",
    ]
    if any(sig in q for sig in shopify_signals):
        return "shopify_management"

    # Analytics checked before social_publishing so "likes on a post" routes correctly
    analytics_signals = [
        "like", "likes", "comment", "comments", "insight", "insights",
        "analytics", "engagement", "reach", "impressions", "saved", "shares",
    ]
    if any(sig in q for sig in analytics_signals):
        return "store_analytics"

    publish_signals = [
        "post", "publish", "caption", "instagram", "facebook",
        "social", "insta", "ig", "fb page", "photo", "image upload",
    ]
    if any(sig in q for sig in publish_signals):
        return "social_publishing"

    # Default to analytics
    return "store_analytics"


# ── Parsing helpers ───────────────────────────────────────────────────────────


def _extract_id(text: str) -> str:
    """Extract the first long numeric ID from a query string."""
    import re
    match = re.search(r"\b(\d{5,})\b", text)
    return match.group(1) if match else ""


def _extract_quoted_text(text: str) -> str:
    """Extract the first single- or double-quoted string."""
    import re
    match = re.search(r"['\"](.+?)['\"]", text)
    return match.group(1) if match else ""

def _extract_product_name(query: str) -> str:
    """Extract a product name from a natural-language query."""
    import re
    # 1) Quoted text
    name = _extract_quoted_text(query)
    if name:
        return name
    # 2) "product <Name>" pattern — stop at prepositions / end
    m = re.search(
        r"(?:product|item)\s+(.+?)(?:\s+(?:from|on|in|at|to)\b|$)",
        query, re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    return ""


async def _resolve_product_id_by_name(query: str) -> str:
    """Look up a Shopify product ID by fuzzy-matching the name in the query."""
    name = _extract_product_name(query)
    if not name:
        return ""
    result = await shopify.get_products(limit=50)
    products = result.get("products", [])
    name_lower = name.lower()
    for p in products:
        title = (p.get("title") or "").lower()
        if name_lower in title or title in name_lower:
            return str(p["id"])
    return ""

def _parse_product_params(query: str) -> dict[str, Any]:
    """Extract product creation parameters from a natural language query."""
    import re

    # 1) Try quoted text first
    title = _extract_quoted_text(query)
    # 2) Try "called/named <title>" patterns (stop at price/description/sku markers)
    if not title:
        named_match = re.search(
            r"(?:called|named|titled)\s+(.+?)(?:\s+(?:priced|for|at|with|costing|\$|description|sku|inventory)|$)",
            query, re.IGNORECASE,
        )
        if named_match:
            title = named_match.group(1).strip()
    # 3) Try "product <Name>" or "create <Name>" pattern
    if not title:
        product_match = re.search(
            r"(?:product|create|add)\s+(?:a\s+)?(?:new\s+)?(?:product\s+)?(.+?)(?:\s+(?:priced|for|at|with|costing|\$|description|sku|on\s+shopify)|$)",
            query, re.IGNORECASE,
        )
        if product_match:
            candidate = product_match.group(1).strip()
            # Don't use if it looks like a verb/action
            if candidate and not candidate.lower().startswith(("on", "in", "to", "from")):
                title = candidate
    # 4) Fallback
    if not title:
        title = "New Product"

    # Extract price — multiple patterns for robustness
    # First try explicit patterns like "priced at $X", "for $X", "at $X", "$X"
    price = "0.00"
    price_patterns = [
        r"(?:priced\s+at|price\s+(?:of|to|at|is)?|for|at|costing)\s+\$?([\d]+(?:\.[\d]{1,2})?)(?:\s*(?:USD|usd))?",
        r"\$([\d]+(?:\.[\d]{1,2})?)",
        r"([\d]+\.[\d]{2})\s*(?:USD|usd|dollars)",
    ]
    # Search in the text after the title to avoid matching numbers in the title
    price_region = query
    if title and title != "New Product":
        idx = query.lower().find(title.lower())
        if idx >= 0:
            price_region = query[idx + len(title):]
    for pattern in price_patterns:
        price_match = re.search(pattern, price_region, re.IGNORECASE)
        if price_match:
            price = price_match.group(1)
            break

    sku_match = re.search(r"\bSKU[:\-\s]*([A-Z0-9\-]+)\b", query, re.IGNORECASE)
    sku = sku_match.group(1) if sku_match else ""

    inv_match = re.search(r"\b(\d+)\s*(?:units?|in stock|qty|quantity)\b", query, re.IGNORECASE)
    inventory = int(inv_match.group(1)) if inv_match else 0

    vendor = ""
    vendor_match = re.search(
        r"(?:vendor|by|from)\s+([A-Z][A-Za-z0-9_\- ]{1,40}?)(?:\s+(?:priced|with|sku|inventory|tags?|description|and|,|\.)|$)",
        query,
    )
    if vendor_match:
        vendor = vendor_match.group(1).strip()

    tags = ""
    tags_match = re.search(
        r"(?:tags?|tagged)[:\s]+([A-Za-z0-9_\-,\s]+?)(?:\s+(?:priced|with|sku|inventory|vendor|description|and)|\.|$)",
        query, re.IGNORECASE,
    )
    if tags_match:
        tags = tags_match.group(1).strip().rstrip(",")

    # Extract description — support many phrasing patterns
    description = ""
    desc_patterns = [
        r"(?:description|described\s+as|desc)[:\s]+(.+?)(?:\s+(?:sku|inventory|priced)|$)",
        r"(?:with\s+description|highlighting|featuring|features)[:\s]+(.+?)(?:\s+(?:sku|inventory|priced)|$)",
        r"description[:\s]+['\"](.+?)['\"]",
    ]
    for pattern in desc_patterns:
        desc_match = re.search(pattern, query, re.IGNORECASE)
        if desc_match:
            description = desc_match.group(1).strip().rstrip(".")
            break

    return {
        "title": title,
        "price": price,
        "sku": sku,
        "inventory": inventory,
        "description": description,
        "vendor": vendor,
        "tags": tags,
    }


def _parse_publish_params(query: str) -> tuple[str, str]:
    """Extract image_url and caption from a natural language query."""
    import re

    url_match = re.search(r"https?://\S+", query)
    image_url = url_match.group(0) if url_match else ""

    caption = _extract_quoted_text(query) or ""

    return image_url, caption


# ── Error helpers ─────────────────────────────────────────────────────────────


def _task_failed(task_id: str, error: str) -> dict[str, Any]:
    return {
        "id": task_id,
        "status": {
            "state": "failed",
            "message": {
                "role": "agent",
                "parts": [{"type": "text", "text": f"Task failed: {error}"}],
            },
        },
    }
