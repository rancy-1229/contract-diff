from sqlalchemy.orm import Session
from app.models.comparison import Comparison
from app.schemas.comparison import ComparisonCreate
from typing import List, Optional
from uuid import UUID

class ComparisonService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_comparison(self, comparison_data: dict) -> Comparison:
        """创建对比任务"""
        comparison = Comparison(**comparison_data)
        self.db.add(comparison)
        self.db.commit()
        self.db.refresh(comparison)
        return comparison
    
    async def get_comparison(self, comparison_id: str) -> Optional[Comparison]:
        """获取对比任务"""
        return self.db.query(Comparison).filter(Comparison.id == UUID(comparison_id)).first()
    
    async def list_comparisons(self) -> List[Comparison]:
        """获取对比任务列表"""
        return self.db.query(Comparison).order_by(Comparison.created_at.desc()).all()
    
    async def update_comparison_status(self, comparison_id: str, status: str) -> Optional[Comparison]:
        """更新对比任务状态"""
        comparison = await self.get_comparison(comparison_id)
        if comparison:
            comparison.status = status
            self.db.commit()
            self.db.refresh(comparison)
        return comparison
