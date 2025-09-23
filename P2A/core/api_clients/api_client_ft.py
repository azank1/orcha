import os
import time
from typing import Tuple, Any, Dict
import httpx
import logging

logger = logging.getLogger(__name__)


class ApiClientFT:
    """FoodTec API client with Basic Auth, retries, and timeout handling"""
    
    def __init__(self, base: str | None = None, timeout: float = 5.0, retries: int = 2):
        self.base = base or os.getenv("FOODTEC_BASE")
        self.user = os.getenv("FOODTEC_USER")
        self.menu_pass = os.getenv("FOODTEC_MENU_PASS")
        self.validate_pass = os.getenv("FOODTEC_VALIDATE_PASS")
        self.accept_pass = os.getenv("FOODTEC_ACCEPT_PASS")
        self.timeout = timeout
        self.retries = retries
        
        if not self.base:
            raise RuntimeError("FOODTEC_BASE must be set for FoodTec client")
        if not self.user:
            raise RuntimeError("FOODTEC_USER must be set for FoodTec client")
        if not self.menu_pass or not self.validate_pass or not self.accept_pass:
            raise RuntimeError("FOODTEC_MENU_PASS, FOODTEC_VALIDATE_PASS, and FOODTEC_ACCEPT_PASS must be set for FoodTec client")
            
        logger.info("[FoodTec] Client initialized with base: %s", self.base)

    def _auth(self, password: str | None = None):
        """Return Basic Auth tuple with specified password"""
        if self.user and password:
            return (self.user, password)
        return None

    def _url(self, path: str) -> str:
        """Construct full URL from base and path"""
        return f"{self.base.rstrip('/')}/{path.lstrip('/')}"

    def get(self, path: str, params: Dict[str, Any] | None = None, password: str | None = None) -> Tuple[int, Any]:
        """GET request with retry logic on 5xx errors or timeouts"""
        url = self._url(path)
        attempt = 0
        last_exc = None
        start = time.time()
        
        while attempt <= self.retries:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    auth = self._auth(password)
                    resp = client.get(url, params=params, auth=auth)
                    duration = time.time() - start
                    logger.info("[FoodTec] GET %s → %d (%dms)", url, resp.status_code, int(duration * 1000))
                    
                    try:
                        return resp.status_code, resp.json()
                    except Exception:
                        return resp.status_code, resp.text
                        
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as exc:
                last_exc = exc
                attempt += 1
                
                # Retry on timeout or 5xx errors
                if (isinstance(exc, httpx.TimeoutException) or 
                    (hasattr(exc, 'response') and exc.response and exc.response.status_code >= 500)):
                    if attempt <= self.retries:
                        logger.warning("[FoodTec] GET retry %s attempt %d due to %s", url, attempt, type(exc).__name__)
                        time.sleep(0.5)  # Brief delay between retries
                        continue
                
                # Don't retry on other errors
                logger.error("[FoodTec] GET failed %s: %s", url, exc)
                raise exc
                
        raise last_exc

    def post(self, path: str, json: Dict[str, Any] | None = None, headers: Dict[str, str] | None = None, password: str | None = None) -> Tuple[int, Any]:
        """POST request with retry logic on 5xx errors or timeouts"""
        url = self._url(path)
        attempt = 0
        last_exc = None
        start = time.time()
        
        while attempt <= self.retries:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    auth = self._auth(password)
                    resp = client.post(url, json=json, headers=headers or {}, auth=auth)
                    duration = time.time() - start
                    logger.info("[FoodTec] POST %s → %d (%dms)", url, resp.status_code, int(duration * 1000))
                    
                    try:
                        return resp.status_code, resp.json()
                    except Exception:
                        return resp.status_code, resp.text
                        
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as exc:
                last_exc = exc
                attempt += 1
                
                # Retry on timeout or 5xx errors
                if (isinstance(exc, httpx.TimeoutException) or 
                    (hasattr(exc, 'response') and exc.response and exc.response.status_code >= 500)):
                    if attempt <= self.retries:
                        logger.warning("[FoodTec] POST retry %s attempt %d due to %s", url, attempt, type(exc).__name__)
                        time.sleep(0.5)  # Brief delay between retries
                        continue
                
                # Don't retry on other errors
                logger.error("[FoodTec] POST failed %s: %s", url, exc)
                raise exc
                
        raise last_exc
        
