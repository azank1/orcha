"""Pytest fixtures for ecommerce-automation tests.

Clears all external API credentials before each test so every tool
exercises its mock-fallback branch. No network calls are made.
"""

import pytest


@pytest.fixture(autouse=True)
def clear_api_keys(monkeypatch):
    for var in [
        "SHOPIFY_STORE_URL",
        "SHOPIFY_ACCESS_TOKEN",
        "FB_ACCESS_TOKEN",
        "FB_PAGE_ID",
        "IG_ACCESS_TOKEN",
        "IG_USER_ID",
    ]:
        monkeypatch.delenv(var, raising=False)
