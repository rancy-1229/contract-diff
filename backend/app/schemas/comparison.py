from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class ComparisonCreate(BaseModel):
    standard_document_id: UUID
    target_document_id: UUID
    result_json: Optional[Dict[str, Any]] = None
    status: str = "pending"
    differences_count: int = 0

class ComparisonResponse(BaseModel):
    id: UUID
    standard_document_id: UUID
    target_document_id: UUID
    status: str
    progress: int
    result_json: Optional[Dict[str, Any]] = None
    differences_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ComparisonList(BaseModel):
    comparisons: List[ComparisonResponse]
    total: int
