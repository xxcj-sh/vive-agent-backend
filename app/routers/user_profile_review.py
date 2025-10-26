"""
用户画像定期回顾机制API路由
提供用户画像的定期回顾、报告生成、自动调度等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.database import get_db
from app.services.user_profile_review_service import ProfileReviewService
from app.services.user_profile_learning_service import ProfileLearningService
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.user_profile_history import UserProfileHistory

router = APIRouter(prefix="/profiles/review", tags=["用户画像定期回顾"])


def get_review_service(db: Session = Depends(get_db)) -> ProfileReviewService:
    """获取画像回顾服务实例"""
    return ProfileReviewService(db)


def get_learning_service(db: Session = Depends(get_db)) -> ProfileLearningService:
    """获取画像学习服务实例"""
    return ProfileLearningService(db)


@router.post("/schedule/{user_id}")
async def schedule_review(
    user_id: int,
    review_type: str = Query(..., description="回顾类型: monthly, quarterly, yearly"),
    scheduled_date: Optional[datetime] = Query(None, description="计划回顾日期"),
    current_user: User = Depends(get_current_user),
    service: ProfileReviewService = Depends(get_review_service)
):
    """安排用户画像定期回顾"""
    # 权限检查：用户只能安排自己的回顾，管理员可以安排所有用户的回顾
    if current_user.get("id") != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="权限不足，只能安排自己的回顾")
    
    # 验证回顾类型
    if review_type not in ["monthly", "quarterly", "yearly"]:
        raise HTTPException(status_code=400, detail="无效的回顾类型")
    
    # 安排回顾
    result = await service.schedule_review(user_id, review_type, scheduled_date)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/execute/{user_id}")
async def execute_review(
    user_id: int,
    review_type: str = Query(..., description="回顾类型: monthly, quarterly, yearly"),
    current_user: User = Depends(get_current_user),
    review_service: ProfileReviewService = Depends(get_review_service),
    learning_service: ProfileLearningService = Depends(get_learning_service)
):
    """执行用户画像定期回顾"""
    # 权限检查
    if current_user.get("id") != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="权限不足，只能执行自己的回顾")
    
    # 验证回顾类型
    if review_type not in ["monthly", "quarterly", "yearly"]:
        raise HTTPException(status_code=400, detail="无效的回顾类型")
    
    # 执行季度回顾
    if review_type == "quarterly":
        result = await review_service.perform_quarterly_review(user_id)
    # 执行月度回顾
    elif review_type == "monthly":
        result = await review_service.perform_monthly_review(user_id)
    # 执行年度回顾
    else:
        # 年度回顾可以结合季度和月度回顾
        quarterly_result = await review_service.perform_quarterly_review(user_id)
        monthly_result = await review_service.perform_monthly_review(user_id)
        
        result = {
            "review_type": "yearly",
            "quarterly_review": quarterly_result,
            "monthly_review": monthly_result,
            "combined_insights": await learning_service.generate_profile_insights(user_id),
            "executed_at": datetime.now().isoformat()
        }
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/reminder/{user_id}")
async def get_review_reminder(
    user_id: int,
    review_type: str = Query(..., description="回顾类型: monthly, quarterly, yearly"),
    current_user: User = Depends(get_current_user),
    service: ProfileReviewService = Depends(get_review_service)
):
    """获取用户画像回顾提醒"""
    # 权限检查
    if current_user.get("id") != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="权限不足，只能查看自己的提醒")
    
    # 验证回顾类型
    if review_type not in ["monthly", "quarterly", "yearly"]:
        raise HTTPException(status_code=400, detail="无效的回顾类型")
    
    # 生成提醒
    result = await service.generate_review_reminder(user_id, review_type)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/status/{user_id}")
async def get_review_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户画像回顾状态"""
    # 权限检查
    if current_user.get("id") != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="权限不足，只能查看自己的状态")
    
    # 获取用户画像
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    if not profile:
        return {
            "user_id": user_id,
            "has_profile": False,
            "review_status": "no_profile",
            "next_review_dates": {}
        }
    
    # 计算下次回顾日期
    now = datetime.now()
    
    # 基于最后更新时间计算下次回顾
    last_updated = profile.updated_at or profile.created_at
    
    next_monthly = last_updated + timedelta(days=30)
    next_quarterly = last_updated + timedelta(days=90)
    next_yearly = last_updated + timedelta(days=365)
    
    # 检查是否需要回顾（基于时间）
    review_status = "up_to_date"
    if now > next_yearly:
        review_status = "overdue_yearly"
    elif now > next_quarterly:
        review_status = "overdue_quarterly"
    elif now > next_monthly:
        review_status = "overdue_monthly"
    
    return {
        "user_id": user_id,
        "has_profile": True,
        "profile_id": profile.id,
        "last_updated": last_updated.isoformat(),
        "review_status": review_status,
        "next_review_dates": {
            "monthly": next_monthly.isoformat(),
            "quarterly": next_quarterly.isoformat(),
            "yearly": next_yearly.isoformat()
        },
        "days_since_last_update": (now - last_updated).days
    }


@router.get("/report/{user_id}")
async def get_review_report(
    user_id: int,
    review_type: str = Query("quarterly", description="回顾类型: monthly, quarterly, yearly"),
    current_user: User = Depends(get_current_user),
    review_service: ProfileReviewService = Depends(get_review_service),
    learning_service: ProfileLearningService = Depends(get_learning_service)
):
    """获取用户画像回顾报告"""
    # 权限检查
    if current_user.get("id") != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="权限不足，只能查看自己的报告")
    
    # 验证回顾类型
    if review_type not in ["monthly", "quarterly", "yearly"]:
        raise HTTPException(status_code=400, detail="无效的回顾类型")
    
    # 获取基础回顾结果
    if review_type == "quarterly":
        review_result = await review_service.perform_quarterly_review(user_id)
    elif review_type == "monthly":
        review_result = await review_service.perform_monthly_review(user_id)
    else:  # yearly
        quarterly_result = await review_service.perform_quarterly_review(user_id)
        monthly_result = await review_service.perform_monthly_review(user_id)
        review_result = {
            "quarterly_review": quarterly_result,
            "monthly_review": monthly_result
        }
    
    # 获取洞察报告
    insights = await learning_service.generate_profile_insights(user_id)
    
    # 生成综合报告
    report = {
        "user_id": user_id,
        "review_type": review_type,
        "generated_at": datetime.now().isoformat(),
        "review_result": review_result,
        "profile_insights": insights,
        "recommendations": insights.get("recommendations", []),
        "next_steps": [
            "根据回顾结果更新用户画像",
            "设置下次回顾提醒",
            "跟踪关键指标变化",
            "持续收集用户反馈"
        ]
    }
    
    return report


@router.post("/auto-schedule/{user_id}")
async def setup_auto_review_schedule(
    user_id: int,
    monthly_enabled: bool = Query(True, description="启用月度回顾"),
    quarterly_enabled: bool = Query(True, description="启用季度回顾"),
    yearly_enabled: bool = Query(True, description="启用年度回顾"),
    current_user: User = Depends(get_current_user),
    service: ProfileReviewService = Depends(get_review_service)
):
    """设置用户画像自动回顾调度"""
    # 权限检查
    if current_user.get("id") != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="权限不足，只能设置自己的调度")
    
    # 设置自动调度
    result = await service.setup_auto_review_schedule(
        user_id, monthly_enabled, quarterly_enabled, yearly_enabled
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/batch-review")
async def perform_batch_review(
    user_ids: List[int],
    review_type: str = Query("quarterly", description="回顾类型: monthly, quarterly, yearly"),
    current_user: User = Depends(get_current_user),
    review_service: ProfileReviewService = Depends(get_review_service),
    learning_service: ProfileLearningService = Depends(get_learning_service)
):
    """批量执行用户画像回顾（管理员功能）"""
    # 权限检查：只有管理员可以执行批量回顾
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以执行批量回顾")
    
    # 验证回顾类型
    if review_type not in ["monthly", "quarterly", "yearly"]:
        raise HTTPException(status_code=400, detail="无效的回顾类型")
    
    # 限制批量处理的用户数量
    if len(user_ids) > 50:
        raise HTTPException(status_code=400, detail="批量处理的用户数量不能超过50个")
    
    results = []
    errors = []
    
    for user_id in user_ids:
        try:
            if review_type == "quarterly":
                result = await review_service.perform_quarterly_review(user_id)
            elif review_type == "monthly":
                result = await review_service.perform_monthly_review(user_id)
            else:  # yearly
                quarterly_result = await review_service.perform_quarterly_review(user_id)
                monthly_result = await review_service.perform_monthly_review(user_id)
                result = {
                    "quarterly_review": quarterly_result,
                    "monthly_review": monthly_result
                }
            
            results.append({
                "user_id": user_id,
                "status": "success",
                "result": result
            })
        
        except Exception as e:
            errors.append({
                "user_id": user_id,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "batch_review_results": {
            "total_processed": len(user_ids),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
            "review_type": review_type,
            "executed_at": datetime.now().isoformat()
        }
    }