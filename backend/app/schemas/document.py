from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class DocumentCreate(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    document_type: str
    content_json: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    document_type: str
    status: str
    content_text: Optional[str] = None
    content_json: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DocumentList(BaseModel):
    documents: list[DocumentResponse]
    total: int
