from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    pdf_path = Column(String(500), nullable=True)  # 转换后的PDF路径
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=False)
    document_type = Column(String(20), nullable=False)  # 'standard' or 'target'
    status = Column(String(20), default='uploaded')  # 'uploaded', 'processing', 'processed', 'failed'
    content_text = Column(Text)
    content_json = Column(JSON)
    meta_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
