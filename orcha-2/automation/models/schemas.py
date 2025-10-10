from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SearchItem(BaseModel):
    name: str
    category: str
    price: Optional[float] = None
    sku: Optional[str] = None
    score: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchItem]


class ErrorPayload(BaseModel):
    event: str = Field(default="error")
    source: str
    message: str


class WSMessage(BaseModel):
    event: str
    data: Dict[str, Any]
    llm_source: Optional[str] = None
