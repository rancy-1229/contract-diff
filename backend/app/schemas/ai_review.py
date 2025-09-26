from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class DiffReviewCreate(BaseModel):
    """创建AI审查请求的schema"""
    comparison_id: str
    diff_id: str
    risk_level: Optional[str] = None
    compliance: Optional[str] = None
    review_suggestions: Optional[str] = None
    raw_ai_response: Optional[str] = None

class DiffReviewResponse(BaseModel):
    """AI审查响应的schema"""
    id: int
    comparison_id: UUID
    diff_id: str
    risk_level: str
    compliance: str
    review_suggestions: str
    raw_ai_response: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
