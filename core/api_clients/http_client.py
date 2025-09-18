import httpx


from typing import Any, Optional, Dict, Union


class HTTPError(Exception):
    """Raised for non-2xx HTTP responses.

    Attributes:
        status_code: HTTP status code
        content: response body (text or parsed JSON)
    """

    def __init__(self, status_code: int, content: Any):
        super().__init__(f"HTTP {status_code}: {content}")
        self.status_code = status_code
        self.content = content


class RequestError(Exception):
    """Raised for network / request issues (timeouts, connection errors)."""


class AsyncHTTPClient:
    """Asynchronous HTTP client for basic CRUD operations.

    Parameters:
        base_url: Base URL for the API (e.g. 'https://api.example.com').
        auth_header: Optional Authorization header value (e.g. 'Bearer <token>' or 'Basic <creds>').
        timeout: Default timeout in seconds for requests.
        default_headers: Optional additional headers to include on every request.

    Usage:
        async with AsyncHTTPClient(base_url, auth_header) as client:
            data = await client.get('/v1/categories')
            created = await client.post('/v1/items', json={'name': 'Test'})
    """

    def __init__(
        self,
        base_url: str,
        auth_header: Optional[str] = None,
        timeout: float = 10.0,
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        if httpx is None:
            raise RuntimeError("httpx is required for async HTTP client. Please install httpx.")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        headers = dict(default_headers or {})
        headers.setdefault("Accept", "application/json")
        if auth_header:
            headers["Authorization"] = auth_header

        # create the httpx AsyncClient with base_url and default headers
        self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=self.timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def _handle_response(self, resp: Any) -> Any:
        if 200 <= resp.status_code < 300:
            # try to return parsed JSON where possible, otherwise text
            ct = resp.headers.get("content-type", "")
            if "application/json" in ct:
                try:
                    return resp.json()
                except Exception:
                    return resp.text
            return resp.text
        # non-2xx -> raise HTTPError containing status and text (caller can inspect)
        raise HTTPError(resp.status_code, resp.text)

    async def get(self, endpoint: str, params: Optional[Dict[str, Union[str, int]]] = None, headers: Optional[Dict[str, str]] = None, timeout: Optional[float] = None) -> Any:
        """Perform GET on `endpoint` (relative path) and return parsed body on success.

        Raises:
            RequestError: network-level errors
            HTTPError: non-2xx responses
        """
        try:
            resp = await self._client.get(endpoint, params=params, headers=headers, timeout=timeout)
            return await self._handle_response(resp)
        except httpx.RequestError as exc:
            raise RequestError(str(exc)) from exc

    async def post(self, endpoint: str, json: Optional[Any] = None, data: Optional[Any] = None, headers: Optional[Dict[str, str]] = None, timeout: Optional[float] = None) -> Any:
        """Perform POST on `endpoint` with JSON or form data.

        Prefer `json` for application/json payloads.
        """
        try:
            resp = await self._client.post(endpoint, json=json, data=data, headers=headers, timeout=timeout)
            return await self._handle_response(resp)
        except httpx.RequestError as exc:
            raise RequestError(str(exc)) from exc

    async def put(self, endpoint: str, json: Optional[Any] = None, data: Optional[Any] = None, headers: Optional[Dict[str, str]] = None, timeout: Optional[float] = None) -> Any:
        """Perform PUT on `endpoint` with JSON or form data."""
        try:
            resp = await self._client.put(endpoint, json=json, data=data, headers=headers, timeout=timeout)
            return await self._handle_response(resp)
        except httpx.RequestError as exc:
            raise RequestError(str(exc)) from exc

    async def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None, timeout: Optional[float] = None) -> Any:
        """Perform DELETE on `endpoint`."""
        try:
            resp = await self._client.delete(endpoint, headers=headers, timeout=timeout)
            return await self._handle_response(resp)
        except httpx.RequestError as exc:
            raise RequestError(str(exc)) from exc
