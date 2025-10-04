"""Response models"""

from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


class StandardResponse(BaseModel):
    """Standard JSON response"""

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")


class TanaPasteResponse(BaseModel):
    """Tana paste format response"""

    format: Literal["tana-paste"] = "tana-paste"
    content: str = Field(..., description="Tana paste formatted content")


class DualFormatResponse(BaseModel):
    """Response that can be in either standard JSON or Tana paste format"""

    json: Optional[StandardResponse] = None
    tana_paste: Optional[str] = None
