"""
差异审查结果数据模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class DiffReview(Base):
    """差异审查结果模型"""
    __tablename__ = "diff_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    comparison_id = Column(UUID(as_uuid=True), ForeignKey("comparisons.id"), nullable=False)
    diff_id = Column(String(100), nullable=False, index=True)
    risk_level = Column(String(10), nullable=False)  # 高/中/低
    compliance = Column(String(20), nullable=False)  # 符合/不符合/部分符合
    review_suggestions = Column(Text, nullable=False)
    raw_ai_response = Column(Text)  # AI原始响应
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    comparison = relationship("Comparison", back_populates="diff_reviews")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "comparison_id": self.comparison_id,
            "diff_id": self.diff_id,
            "risk_level": self.risk_level,
            "compliance": self.compliance,
            "review_suggestions": self.review_suggestions,
            "raw_ai_response": self.raw_ai_response,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
