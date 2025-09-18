from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class AgentRole(str, Enum):
    menuHelper = "menuHelper"
    orderHelper = "orderHelper"

class AgentPlatform(str, Enum):
    n8n = "n8n"
    vapi = "vapi"
    zapier = "zapier"
    code = "code"

class Vendor(str, Enum):
    foodtec = "foodtec"
    restarage = "restarage"

class Agent(BaseModel):
    name: str = Field(..., description="Name of the agent")
    role: AgentRole = Field(..., description="Role of the agent")
    platform: AgentPlatform = Field(..., description="Platform where the agent is deployed")
    vendor: Vendor = Field(..., description="Vendor system the agent interacts with")
    credentials: Dict[str, Any] = Field(..., description="Credentials or configuration for the agent")