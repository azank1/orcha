"""Shopify Admin REST API tools — product CRUD.

All functions use Shopify Admin API v2024-04.
Returns mock payloads when SHOPIFY_STORE_URL or SHOPIFY_ACCESS_TOKEN are
absent — unless REQUIRE_LIVE_CREDENTIALS=true, in which case they raise
instead (see ._production_guard).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

_API_VERSION = "2024-04"


def _shopify_headers() -> dict[str, str]:
    # Prefer per-request contextvar (injected by OAuthHeaderMiddleware)
    from ..a2a_server import shopify_access_token
    cv_token = shopify_access_token.get()
    token: str = cv_token if cv_token else (os.getenv("SHOPIFY_ACCESS_TOKEN") or "")
    return {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json",
    }


def _shopify_base() -> str:
    # Prefer per-request contextvar (injected by OAuthHeaderMiddleware)
    from ..a2a_server import shopify_store_url
    cv_url = shopify_store_url.get()
    url: str = cv_url if cv_url else (os.getenv("SHOPIFY_STORE_URL") or "")
    return f"{url.rstrip('/')}/admin/api/{_API_VERSION}"


def _is_configured() -> bool:
    from ._production_guard import require_configured
    from ..a2a_server import shopify_access_token, shopify_store_url
    has_contextvar = bool(shopify_access_token.get()) and bool(shopify_store_url.get())
    has_env = bool(os.getenv("SHOPIFY_STORE_URL")) and bool(os.getenv("SHOPIFY_ACCESS_TOKEN"))
    configured = has_contextvar or has_env
    return require_configured(configured, "Shopify", "SHOPIFY_STORE_URL / SHOPIFY_ACCESS_TOKEN")


def _mock_product(product_id: str = "mock_001", title: str = "Mock Product") -> dict:
    return {
        "id": product_id,
        "title": title,
        "status": "draft",
        "vendor": "Mock Vendor",
        "product_type": "Footwear",
        "variants": [{"id": "var_001", "price": "99.99", "sku": "SKU-001", "inventory_quantity": 50}],
        "tags": "mock, demo",
    }


async def create_product(
    title: str,
    price: str,
    description: str = "",
    sku: str = "",
    inventory: int = 0,
    product_type: str = "",
    vendor: str = "",
    tags: str = "",
) -> dict[str, Any]:
    """Create a new product in the Shopify store."""
    if not _is_configured():
        return {
            "status": "mock",
            "product": {**_mock_product(title=title), "price": price, "body_html": description},
        }
    body = {
        "product": {
            "title": title,
            "body_html": description,
            "vendor": vendor,
            "product_type": product_type,
            "tags": tags,
            "status": "draft",
            "variants": [{"price": price, "sku": sku, "inventory_quantity": inventory}],
        }
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.post(
                f"{_shopify_base()}/products.json",
                headers=_shopify_headers(),
                json=body,
            )
            resp.raise_for_status()
            return {"status": "ok", "product": resp.json().get("product", {})}
        except Exception as exc:
            logger.warning("create_product failed: %s", exc)
            return {"status": "error", "error": str(exc)}


async def get_products(limit: int = 10, status: str = "") -> dict[str, Any]:
    """Fetch a list of products from the Shopify store.

    status: "" (all), "active", "draft", or "archived".
    """
    if not _is_configured():
        return {
            "status": "mock",
            "products": [_mock_product(f"mock_{i:03d}", f"Mock Product {i}") for i in range(1, 4)],
        }
    params: dict[str, Any] = {"limit": limit}
    if status:
        params["status"] = status
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(
                f"{_shopify_base()}/products.json",
                headers=_shopify_headers(),
                params=params,
            )
            resp.raise_for_status()
            return {"status": "ok", "products": resp.json().get("products", [])}
        except Exception as exc:
            logger.warning("get_products failed: %s", exc)
            return {"status": "error", "error": str(exc)}


async def get_product_by_id(product_id: str) -> dict[str, Any]:
    """Get a single Shopify product by ID."""
    if not _is_configured():
        return {"status": "mock", "product": _mock_product(product_id)}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(
                f"{_shopify_base()}/products/{product_id}.json",
                headers=_shopify_headers(),
            )
            resp.raise_for_status()
            return {"status": "ok", "product": resp.json().get("product", {})}
        except Exception as exc:
            logger.warning("get_product_by_id failed id=%s: %s", product_id, exc)
            return {"status": "error", "error": str(exc)}


async def publish_product(product_id: str) -> dict[str, Any]:
    """Publish a Shopify product (set status to active)."""
    if not _is_configured():
        return {"status": "mock", "product": {**_mock_product(product_id), "status": "active"}}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.put(
                f"{_shopify_base()}/products/{product_id}.json",
                headers=_shopify_headers(),
                json={"product": {"id": product_id, "status": "active"}},
            )
            resp.raise_for_status()
            return {"status": "ok", "product": resp.json().get("product", {})}
        except Exception as exc:
            logger.warning("publish_product failed id=%s: %s", product_id, exc)
            return {"status": "error", "error": str(exc)}


async def unpublish_product(product_id: str) -> dict[str, Any]:
    """Unpublish a Shopify product (set status to draft)."""
    if not _is_configured():
        return {"status": "mock", "product": {**_mock_product(product_id), "status": "draft"}}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.put(
                f"{_shopify_base()}/products/{product_id}.json",
                headers=_shopify_headers(),
                json={"product": {"id": product_id, "status": "draft"}},
            )
            resp.raise_for_status()
            return {"status": "ok", "product": resp.json().get("product", {})}
        except Exception as exc:
            logger.warning("unpublish_product failed id=%s: %s", product_id, exc)
            return {"status": "error", "error": str(exc)}


async def delete_product(product_id: str) -> dict[str, Any]:
    """Delete a product from the Shopify store."""
    if not _is_configured():
        return {"status": "mock", "deleted": True, "product_id": product_id}
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.delete(
                f"{_shopify_base()}/products/{product_id}.json",
                headers=_shopify_headers(),
            )
            resp.raise_for_status()
            return {"status": "ok", "deleted": True, "product_id": product_id}
        except Exception as exc:
            logger.warning("delete_product failed id=%s: %s", product_id, exc)
            return {"status": "error", "error": str(exc)}


async def update_product(
    product_id: str,
    *,
    title: str = "",
    price: str = "",
    description: str = "",
    sku: str = "",
    vendor: str = "",
    tags: str = "",
    product_type: str = "",
) -> dict[str, Any]:
    """Update an existing Shopify product (title, price, description, sku,
    vendor, tags, product_type)."""
    if not _is_configured():
        return {"status": "mock", "product": {**_mock_product(product_id), "price": price or "0.00"}}
    product_data: dict[str, Any] = {"id": product_id}
    if title:
        product_data["title"] = title
    if description:
        product_data["body_html"] = description
    if vendor:
        product_data["vendor"] = vendor
    if tags:
        product_data["tags"] = tags
    if product_type:
        product_data["product_type"] = product_type
    # Price + SKU live on variants — update the first variant
    variant_data: dict[str, Any] = {}
    if price:
        variant_data["price"] = price
    if sku:
        variant_data["sku"] = sku
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            if variant_data:
                resp = await client.get(
                    f"{_shopify_base()}/products/{product_id}.json",
                    headers=_shopify_headers(),
                )
                resp.raise_for_status()
                existing = resp.json().get("product", {})
                variants = existing.get("variants", [])
                if variants:
                    variant_data["id"] = variants[0]["id"]
                    product_data["variants"] = [variant_data]
            resp = await client.put(
                f"{_shopify_base()}/products/{product_id}.json",
                headers=_shopify_headers(),
                json={"product": product_data},
            )
            resp.raise_for_status()
            return {"status": "ok", "product": resp.json().get("product", {})}
        except Exception as exc:
            logger.warning("update_product failed id=%s: %s", product_id, exc)
            return {"status": "error", "error": str(exc)}

