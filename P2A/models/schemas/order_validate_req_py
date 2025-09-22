"""OrderValidateRequest model generated from TypeBox schema."""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class OrderValidateRequest(BaseModel):
    request_id: Optional[str] = None
    idem: Optional[str] = None
    store_id: str
    items: List[Dict[str, Any]]
    customer: Dict[str, Any]
    payment: Optional[Dict[str, Any]] = None
