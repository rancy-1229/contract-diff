from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.document_service import DocumentService
from app.utils.file_parser import DocumentParser
from app.schemas.document import DocumentResponse, DocumentList
import os
import uuid
from app.config import settings

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),  # "standard" or "target"
    db: Session = Depends(get_db)
):
    """上传文档"""
    # 验证文件类型
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="只支持 PDF 和 Word 格式文件")
    
    # 验证文件大小
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 50MB")
    
    # 生成唯一文件名
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # 保存文件到本地
    file_path = os.path.join(settings.DOCUMENTS_DIR, document_type, unique_filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    # 解析文档
    try:
        parser = DocumentParser()
        parsed_data = await parser.parse_document(file_path, file.content_type)
        print(f"[DEBUG] 解析后的数据: {parsed_data}")
        
        # 保存到数据库
        document_service = DocumentService(db)
        document = await document_service.create_document({
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": file_path,
            "pdf_path": parsed_data.get("pdf_path"),  # 保存PDF路径
            "file_size": len(content),
            "file_type": file.content_type,
            "document_type": document_type,
            "content_json": parsed_data,
            "status": "processed"
        })
        
        return {
            "document_id": str(document.id),
            "filename": file.filename,
            "document_type": document_type,
            "status": "uploaded",
            "file_size": len(content)
        }
        
    except Exception as e:
        # 删除已上传的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

@router.get("/", response_model=DocumentList)
async def list_documents(db: Session = Depends(get_db)):
    """获取文档列表"""
    document_service = DocumentService(db)
    documents = await document_service.list_documents()
    return DocumentList(documents=documents, total=len(documents))

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """获取文档信息"""
    document_service = DocumentService(db)
    document = await document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    return document

@router.delete("/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """删除文档"""
    document_service = DocumentService(db)
    document = await document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 删除文件
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # 删除数据库记录
    await document_service.delete_document(document_id)
    
    return {"message": "文档删除成功"}

@router.get("/{document_id}/pdf")
async def get_document_pdf(document_id: str, db: Session = Depends(get_db)):
    """获取文档的PDF文件"""
    document_service = DocumentService(db)
    document = await document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 确定PDF文件路径
    pdf_path = document.pdf_path or document.file_path
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF文件不存在")
    
    # 返回PDF文件
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=document.original_filename or document.filename
    )
