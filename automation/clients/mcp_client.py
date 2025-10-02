import httpx
import uuid
import time
import json
from typing import Any, Dict, Optional

class MCPClient:
    def __init__(self, url: str = "http://127.0.0.1:9090/rpc"):
        """
        Initialize the MCP client
        
        Args:
            url: The URL of the MCP JSON-RPC endpoint (default: http://127.0.0.1:9090/rpc)
        """
        self.url = url

    def call(self, method: str, params: dict, idempotency_key: Optional[str] = None) -> dict:
        """
        Make a JSON-RPC call to the MCP server
        
        Args:
            method: The RPC method to call
            params: The parameters to pass to the method
            idempotency_key: Optional idempotency key for non-idempotent operations
            
        Returns:
            The parsed JSON response
            
        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        # Create unique request ID with timestamp
        timestamp = int(time.time() * 1000)
        request_id = f"automation-{timestamp}"
        
        # Create request payload
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        # Setup headers
        headers = {
            "Content-Type": "application/json",
            "X-Request-ID": str(uuid.uuid4())
        }
        
        # Add idempotency key if provided
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        
        with httpx.Client(timeout=10.0) as client:
            try:
                response = client.post(
                    self.url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                # Parse the JSON response
                result = response.json()
                
                # Check for JSON-RPC errors
                if "error" in result:
                    error = result["error"]
                    error_message = error.get('message', 'Unknown error')
                    error_code = error.get('code', 'No code')
                    raise Exception(f"JSON-RPC error {error_code}: {error_message}")
                
                return result
                
            except httpx.ConnectError as e:
                print(f"Connection error details: {str(e)}")
                raise ConnectionError(f"Could not connect to MCP server at {self.url}. Is the server running?")
            except httpx.TimeoutException:
                raise TimeoutError(f"Request to MCP server timed out after 10 seconds")
            except httpx.HTTPStatusError as e:
                raise Exception(f"HTTP error: {e.response.status_code} - {e.response.reason_phrase}")
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON response from MCP server")