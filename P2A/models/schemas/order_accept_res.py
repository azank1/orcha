"""OrderAcceptResponse model generated from TypeBox schema."""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class OrderAcceptResponse(BaseModel):
    ok: bool
    order_id: str
    eta: Optional[str] = None
    idem: str
