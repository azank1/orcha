import httpx
import os
import base64
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv


class FoodTecAPIClient:
    """HTTP client for FoodTec API - exact copy of working client.py"""
    
    def __init__(self):
        load_dotenv()
        
        self.base_url = os.getenv('FOODTEC_BASE', '').rstrip('/')
        if not self.base_url:
            raise ValueError("FOODTEC_BASE environment variable required")
            
        self.user = os.getenv('FOODTEC_USER', 'apiclient')
        
        # Individual passwords per endpoint
        self.menu_pass = os.getenv('FOODTEC_MENU_PASS')
        self.validate_pass = os.getenv('FOODTEC_VALIDATE_PASS')
        self.accept_pass = os.getenv('FOODTEC_ACCEPT_PASS')
        
        # Validate required passwords
        for name, password in [
            ('FOODTEC_MENU_PASS', self.menu_pass),
            ('FOODTEC_VALIDATE_PASS', self.validate_pass),
            ('FOODTEC_ACCEPT_PASS', self.accept_pass)
        ]:
            if not password:
                raise ValueError(f"Missing required environment variable: {name}")
    
    
    def _auth_header(self, password: str) -> str:
        """Generate Basic Auth header."""
        token = base64.b64encode(f"{self.user}:{password}".encode()).decode()
        return f"Basic {token}"
    
    def _common_headers(self) -> Dict[str, str]:
        """Standard headers for all requests."""
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _request(self, method: str, path: str, password: str, json_data: Any = None, params: Dict[str, Any] = None) -> Tuple[int, Any, str]:
        """Execute HTTP request with standard error handling."""
        url = f"{self.base_url}{path}"
        headers = self._common_headers()
        headers['Authorization'] = self._auth_header(password)
        
        with httpx.Client(timeout=15.0) as client:
            response = client.request(method, url, headers=headers, json=json_data, params=params)
            
            try:
                json_response = response.json()
            except Exception:
                json_response = None
                
            return response.status_code, json_response, response.text
    
    def get_menu(self, order_type: str = "Pickup") -> Tuple[int, Any, str]:
        """
        Fetch menu categories from FoodTec API.
        
        Args:
            order_type: Type of order (default: "Pickup")
            
        Returns:
            Tuple of (status_code, json_data, raw_text)
        """
        return self._request(
            "GET", 
            "/menu/categories", 
            self.menu_pass,
            params={"orderType": order_type}
        )
    
    def validate_order(self, order_payload: Dict[str, Any]) -> Tuple[int, Any, str]:
        """
        Validate order with FoodTec API.
        
        Args:
            order_payload: Order data following FoodTec v1 validation schema
            
        Returns:
            Tuple of (status_code, json_data, raw_text)
        """
        return self._request(
            "POST",
            "/validate/order",
            self.validate_pass,
            json_data=order_payload
        )
    
    def accept_order(self, order_payload: Dict[str, Any]) -> Tuple[int, Any, str]:
        """
        Accept order with FoodTec API.
        
        Args:
            order_payload: Order data following FoodTec v2 acceptance schema
            
        Returns:
            Tuple of (status_code, json_data, raw_text)
        """
        return self._request(
            "POST",
            "/orders", 
            self.accept_pass,
            json_data=order_payload
        )