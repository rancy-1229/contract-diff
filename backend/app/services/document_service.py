from sqlalchemy.orm import Session
from app.models.document import Document
from app.schemas.document import DocumentCreate
from typing import List, Optional
from uuid import UUID

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_document(self, document_data: dict) -> Document:
        """创建文档记录"""
        document = Document(**document_data)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """获取文档"""
        return self.db.query(Document).filter(Document.id == UUID(document_id)).first()
    
    async def list_documents(self) -> List[Document]:
        """获取文档列表"""
        return self.db.query(Document).order_by(Document.created_at.desc()).all()
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        document = await self.get_document(document_id)
        if document:
            self.db.delete(document)
            self.db.commit()
            return True
        return False
    
    async def update_document_status(self, document_id: str, status: str) -> Optional[Document]:
        """更新文档状态"""
        document = await self.get_document(document_id)
        if document:
            document.status = status
            self.db.commit()
            self.db.refresh(document)
        return document
    
    async def update_document_pdf_path(self, document_id: str, pdf_path: str) -> Optional[Document]:
        """更新文档PDF路径"""
        document = await self.get_document(document_id)
        if document:
            document.pdf_path = pdf_path
            self.db.commit()
            self.db.refresh(document)
        return document