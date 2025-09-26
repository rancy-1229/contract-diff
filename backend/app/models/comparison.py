from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Comparison(Base):
    __tablename__ = "comparisons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    standard_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    target_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    status = Column(String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    progress = Column(Integer, default=0)
    result_json = Column(JSON)
    differences_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # 关系
    standard_document = relationship("Document", foreign_keys=[standard_document_id])
    target_document = relationship("Document", foreign_keys=[target_document_id])
    diff_reviews = relationship("DiffReview", back_populates="comparison", cascade="all, delete-orphan")
