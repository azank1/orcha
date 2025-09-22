"""OrderValidateResponse model generated from TypeBox schema."""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class OrderValidateResponse(BaseModel):
    ok: bool
    draft: Optional[Dict[str, Any]] = None
    issues: Optional[List[Dict[str, Any]]] = None
