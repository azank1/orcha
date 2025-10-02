import httpx
from typing import Any, Dict

class ProxyClient:
    def __init__(self, base_url="http://127.0.0.1:8080"):
        self.base_url = base_url
    
    async def call_endpoint(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a specific endpoint on the proxy server
        
        Args:
            endpoint: The endpoint to call (e.g., '/menu', '/order')
            data: The data to send in the request body
            
        Returns:
            The JSON response from the proxy
        """
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base_url}{endpoint}", json=data)
            r.raise_for_status()
            return r.json()