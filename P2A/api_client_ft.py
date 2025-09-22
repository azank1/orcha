from __future__ import annotations
import os
import time
from typing import Any, Dict, Optional, Tuple

import httpx


class ApiClientFT:
    """Thin FoodTec API client with Basic Auth, timeouts, and basic retries.

    Reads configuration from environment by default:
      - FOODTEC_BASE (e.g., https://host/ws/store/v1)
      - FOODTEC_USER
      - FOODTEC_PASS

    Methods do not raise on non-2xx; they return (status_code, parsed_json_or_text).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        *,
        timeout: float = 10.0,
        retries: int = 2,
    ) -> None:
        self.base_url = (base_url or os.getenv("FOODTEC_BASE", "")).rstrip("/")
        self.username = username or os.getenv("FOODTEC_USER", "")
        self.password = password or os.getenv("FOODTEC_PASS", "")
        self.timeout = timeout
        self.retries = retries

        # Build a client with default headers; auth provided per-request via BasicAuth tuple
        self._client = httpx.Client(timeout=self.timeout)

    def _request(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None, json: Any = None, headers: Optional[Dict[str, str]] = None) -> Tuple[int, Any]:
        url = f"{self.base_url}{path}"
        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt <= self.retries:
            try:
                resp = self._client.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    headers=headers,
                    auth=(self.username, self.password) if (self.username or self.password) else None,
                )
                # Try to parse json; fallback to text
                data: Any
                try:
                    data = resp.json()
                except Exception:
                    data = resp.text
                return resp.status_code, data
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.NetworkError) as exc:
                last_exc = exc
                attempt += 1
                if attempt > self.retries:
                    return 599, {"error": str(exc)}
                time.sleep(0.2 * attempt)
            except Exception as exc:  # other unexpected errors
                return 598, {"error": str(exc)}

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Tuple[int, Any]:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: Any = None, headers: Optional[Dict[str, str]] = None) -> Tuple[int, Any]:
        return self._request("POST", path, json=json, headers=headers)
