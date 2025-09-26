from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.comparison_service import ComparisonService
from app.services.document_service import DocumentService
from app.services.ai_review_service import AIReviewService
from app.utils.diff_engine import DiffEngine
from app.utils.image_processor import ImageProcessor
from app.schemas.comparison import ComparisonResponse, ComparisonList
from pydantic import BaseModel
from uuid import UUID

router = APIRouter(prefix="/api/comparisons", tags=["comparisons"])

class ComparisonRequest(BaseModel):
    standard_document_id: UUID
    target_document_id: UUID
    enable_ai_review: bool = True  # 是否启用AI审查

@router.post("/", response_model=dict)
async def create_comparison(
    request: ComparisonRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """创建文档对比任务"""
    # 获取文档信息
    document_service = DocumentService(db)
    standard_doc = await document_service.get_document(str(request.standard_document_id))
    target_doc = await document_service.get_document(str(request.target_document_id))
    
    if not standard_doc or not target_doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if standard_doc.status != "processed" or target_doc.status != "processed":
        raise HTTPException(status_code=400, detail="文档尚未处理完成")
    
    try:
        # 执行差异对比
        diff_engine = DiffEngine()
        comparison_result = await diff_engine.compare_documents(
            standard_doc.content_json,
            target_doc.content_json
        )
        
        # 生成对比图片（传递差异列表用于绘制标记）
        image_processor = ImageProcessor()
        images = await image_processor.generate_comparison_images(
            standard_doc.pdf_path or standard_doc.file_path,
            target_doc.pdf_path or target_doc.file_path,
            f"comp_{request.standard_document_id}_{request.target_document_id}",
            comparison_result["diff_list"]  # 传递差异列表
        )
        
        # 将AI审查标志添加到结果中
        comparison_result["ai_review_enabled"] = request.enable_ai_review
        
        # 保存对比结果
        comparison_service = ComparisonService(db)
        comparison = await comparison_service.create_comparison({
            "standard_document_id": request.standard_document_id,
            "target_document_id": request.target_document_id,
            "result_json": comparison_result,
            "status": "completed",
            "differences_count": len(comparison_result["diff_list"])
        })
        
        # 如果启用AI审查，启动后台任务
        print(f"[DEBUG] AI审查检查: enable_ai_review={request.enable_ai_review}, diff_list长度={len(comparison_result['diff_list'])}")
        if request.enable_ai_review and comparison_result["diff_list"]:
            print(f"[DEBUG] 启动AI审查后台任务: comparison_id={comparison.id}")
            from app.api.ai_review import _perform_batch_ai_review
            background_tasks.add_task(_perform_batch_ai_review, db, str(comparison.id), comparison_result["diff_list"])
        else:
            print(f"[DEBUG] 未启动AI审查: enable_ai_review={request.enable_ai_review}, diff_list存在={bool(comparison_result['diff_list'])}")
        
        return {
            "comparison_id": str(comparison.id),
            "standard_pdf_url": f"/api/documents/{request.standard_document_id}/pdf",
            "target_pdf_url": f"/api/documents/{request.target_document_id}/pdf",
            "standard_images": images["standard_images"],  # 保留向后兼容
            "target_images": images["target_images"],      # 保留向后兼容
            "diff_list": comparison_result["diff_list"],
            "summary": comparison_result["summary"],
            "ai_review_enabled": request.enable_ai_review,
            "page_count": len(images["standard_images"])  # 添加页数信息
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比处理失败: {str(e)}")

@router.get("/", response_model=ComparisonList)
async def list_comparisons(db: Session = Depends(get_db)):
    """获取对比任务列表"""
    comparison_service = ComparisonService(db)
    comparisons = await comparison_service.list_comparisons()
    return ComparisonList(comparisons=comparisons, total=len(comparisons))

@router.get("/{comparison_id}", response_model=dict)
async def get_comparison_result(comparison_id: str, db: Session = Depends(get_db)):
    """获取对比结果"""
    comparison_service = ComparisonService(db)
    comparison = await comparison_service.get_comparison(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="对比任务不存在")
    
    return {
        "comparison_id": str(comparison.id),
        "standard_document_id": str(comparison.standard_document_id),
        "target_document_id": str(comparison.target_document_id),
        "status": comparison.status,
        "diff_list": comparison.result_json["diff_list"],
        "summary": comparison.result_json["summary"],
        "created_at": comparison.created_at
    }
