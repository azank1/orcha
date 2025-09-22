"""MenuExportResponse model generated from TypeBox schema."""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class MenuExportResponse(BaseModel):
    menu: Dict[str, Any]
    page: int
    page_size: int
    total: int
