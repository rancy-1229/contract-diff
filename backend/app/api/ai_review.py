from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict
import asyncio
import time

from app.database import get_db
from app.models.comparison import Comparison
from app.models.diff_review import DiffReview
from app.services.ai_review_service import AIReviewService
from app.schemas.ai_review import DiffReviewResponse, DiffReviewCreate

router = APIRouter(
    prefix="/api/ai-review",
    tags=["AI Review"]
)

ai_review_service = AIReviewService()

async def _perform_batch_ai_review(db: Session, comparison_id: str, diff_list: List[Dict]):
    """批量执行AI审查并保存结果"""
    print(f"[DEBUG] 开始执行AI审查后台任务: comparison_id={comparison_id}, diff_list长度={len(diff_list)}")
    try:
        from uuid import UUID
        from app.models.document import Document
        
        comparison_uuid = UUID(comparison_id)
        
        # 获取对比结果以获取文档ID
        comparison = db.query(Comparison).filter(Comparison.id == comparison_uuid).first()
        if not comparison:
            print(f"[DEBUG] Comparison {comparison_id} not found")
            return
        
        print(f"[DEBUG] 找到对比: {comparison.id}, 状态: {comparison.status}")
        
        # 获取文档内容
        standard_doc = db.query(Document).filter(Document.id == comparison.standard_document_id).first()
        target_doc = db.query(Document).filter(Document.id == comparison.target_document_id).first()
        
        print(f"[DEBUG] 标准文档: {standard_doc.id if standard_doc else 'None'}, 目标文档: {target_doc.id if target_doc else 'None'}")
        
        standard_doc_content = standard_doc.content_json if standard_doc else None
        target_doc_content = target_doc.content_json if target_doc else None
        
        print(f"[DEBUG] 标准文档内容存在: {standard_doc_content is not None}, 目标文档内容存在: {target_doc_content is not None}")
        
        # 检查是否已存在审查结果
        existing_reviews = db.query(DiffReview).filter(
            DiffReview.comparison_id == comparison_uuid
        ).all()
        existing_diff_ids = {review.diff_id for review in existing_reviews}
        
        print(f"[DEBUG] 已存在的审查结果数量: {len(existing_reviews)}")
        
        # 过滤出未审查的差异
        unreviewed_diffs = []
        for diff in diff_list:
            diff_id = diff.get("element_id") or diff.get("diff_id")
            if diff_id not in existing_diff_ids:
                unreviewed_diffs.append(diff)
        
        print(f"[DEBUG] 未审查的差异数量: {len(unreviewed_diffs)}")
        
        if not unreviewed_diffs:
            print(f"[DEBUG] All diffs already reviewed for comparison {comparison_id}")
            return
        
        print(f"Performing batch AI review for {len(unreviewed_diffs)} diffs")
        
        # 批量调用AI审查
        print(f"[DEBUG] 开始调用AI审查服务...")
        review_results = await ai_review_service.review_multiple_diffs(
            unreviewed_diffs, 
            standard_doc_content, 
            target_doc_content
        )
        
        print(f"[DEBUG] AI审查服务返回结果数量: {len(review_results)}")
        
        # 处理并保存审查结果
        saved_count = 0
        for result in review_results:
            print(f"[DEBUG] 处理AI审查结果: {result}")
            # 处理AI返回的结果
            processed_result = _process_ai_review_result(result)
            print(f"[DEBUG] 处理后的结果: {processed_result}")
            
            db_review = DiffReview(
                comparison_id=comparison_uuid,
                diff_id=processed_result["diff_id"],
                risk_level=processed_result["risk_level"],
                compliance=processed_result["compliance"],
                review_suggestions=processed_result["review_suggestions"],
                raw_ai_response=processed_result["raw_ai_response"]
            )
            db.add(db_review)
            saved_count += 1
        
        print(f"[DEBUG] 准备提交 {saved_count} 条AI审查结果到数据库...")
        db.commit()
        print(f"[DEBUG] 成功保存 {saved_count} 条AI审查结果 for comparison {comparison_id}")
        
    except Exception as e:
        print(f"Batch AI review failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()

def _process_ai_review_result(result: Dict) -> Dict:
    """处理AI审查结果，确保数据格式正确"""
    processed = {
        "diff_id": result.get("diff_id", ""),
        "risk_level": result.get("risk_level", "中"),
        "compliance": result.get("compliance", "符合"),
        "review_suggestions": result.get("review_suggestions", "暂无审查意见"),
        "raw_ai_response": result.get("raw_ai_response", "")
    }
    
    # 确保diff_id不为空
    if not processed["diff_id"]:
        processed["diff_id"] = f"diff_{int(time.time())}"
    
    # 确保风险级别是有效值
    if processed["risk_level"] not in ["高", "中", "低"]:
        processed["risk_level"] = "中"
    
    # 确保合规性是有效值
    if processed["compliance"] not in ["符合", "不符合", "部分符合"]:
        processed["compliance"] = "符合"
    
    return processed

@router.post("/comparisons/{comparison_id}/review", response_model=List[DiffReviewResponse])
async def start_ai_review(
    comparison_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    针对指定对比结果中的所有差异启动AI审查。
    审查过程将在后台运行。
    """
    from uuid import UUID
    try:
        comparison_uuid = UUID(comparison_id)
        comparison = db.query(Comparison).filter(Comparison.id == comparison_uuid).first()
        if not comparison:
            raise HTTPException(status_code=404, detail="Comparison not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid comparison ID format")

    if not comparison.result_json or not comparison.result_json.get("diff_list"):
        raise HTTPException(status_code=400, detail="No differences found in comparison result to review.")

    diff_list = comparison.result_json["diff_list"]
    
    # 启动后台任务进行AI审查
    background_tasks.add_task(_perform_batch_ai_review, db, comparison_id, diff_list)
    
    return await get_ai_reviews(comparison_id, db)

@router.get("/comparisons/{comparison_id}/review", response_model=List[DiffReviewResponse])
async def get_ai_reviews(
    comparison_id: str,
    db: Session = Depends(get_db)
):
    """
    获取指定对比结果的所有AI审查意见。
    """
    from uuid import UUID
    try:
        # 将字符串转换为UUID
        comparison_uuid = UUID(comparison_id)
        
        # 检查对比是否存在
        comparison = db.query(Comparison).filter(Comparison.id == comparison_uuid).first()
        if not comparison:
            raise HTTPException(status_code=404, detail="Comparison not found")
        
        # 检查是否启用了AI审查
        ai_review_enabled = comparison.result_json.get('ai_review_enabled', False) if comparison.result_json else False
        print(f"[DEBUG] 查询AI审查结果: comparison_id={comparison_id}, ai_review_enabled={ai_review_enabled}")
        
        reviews = db.query(DiffReview).filter(DiffReview.comparison_id == comparison_uuid).all()
        print(f"[DEBUG] 找到 {len(reviews)} 条AI审查结果")
        
        return reviews
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid comparison ID format")

@router.delete("/comparisons/{comparison_id}/review/{diff_id}", status_code=204)
async def delete_ai_review(
    comparison_id: str,
    diff_id: str,
    db: Session = Depends(get_db)
):
    """
    删除指定差异的AI审查意见。
    """
    review = db.query(DiffReview).filter(
        DiffReview.comparison_id == comparison_id,
        DiffReview.diff_id == diff_id
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="AI review not found")
    
    db.delete(review)
    db.commit()
    return {"message": "AI review deleted successfully"}