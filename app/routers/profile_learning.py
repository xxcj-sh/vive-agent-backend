"""
用户画像智能学习API路由
提供用户画像的智能分析、学习、洞察生成等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.services.profile_learning_service import ProfileLearningService
from app.services.profile_review_service import ProfileReviewService
from app.utils.auth import get_current_user
from app.models.user import User
from datetime import datetime

router = APIRouter(prefix="/profiles/learning", tags=["用户画像智能学习"])


def get_learning_service(db: Session = Depends(get_db)) -> ProfileLearningService:
    """获取画像学习服务实例"""
    return ProfileLearningService(db)


def get_review_service(db: Session = Depends(get_db)) -> ProfileReviewService:
    """获取画像回顾服务实例"""
    return ProfileReviewService(db)


@router.post("/analyze-interaction")
async def analyze_user_interaction(
    interaction_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    service: ProfileLearningService = Depends(get_learning_service)
):
    """分析用户交互行为"""
    # 验证交互数据
    if not interaction_data or "type" not in interaction_data:
        raise HTTPException(status_code=400, detail="交互数据格式错误")
    
    # 分析交互
    result = await service.analyze_user_interaction(current_user.id, interaction_data)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/behavioral-learning")
async def perform_behavioral_learning(
    time_window: str = Query("30d", description="时间窗口: 7d, 30d, 90d"),
    current_user: User = Depends(get_current_user),
    service: ProfileLearningService = Depends(get_learning_service)
):
    """基于用户行为模式进行学习"""
    # 执行行为学习
    result = await service.perform_behavioral_learning(current_user.id, time_window)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/contextual-learning")
async def perform_contextual_learning(
    context_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    service: ProfileLearningService = Depends(get_learning_service)
):
    """基于上下文信息进行学习"""
    # 验证上下文数据
    if not context_data or "type" not in context_data:
        raise HTTPException(status_code=400, detail="上下文数据格式错误")
    
    # 执行上下文学习
    result = await service.perform_contextual_learning(current_user.id, context_data)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.get("/generate-insights")
async def generate_profile_insights(
    current_user: User = Depends(get_current_user),
    service: ProfileLearningService = Depends(get_learning_service)
):
    """生成用户画像洞察报告"""
    # 生成洞察
    result = await service.generate_profile_insights(current_user.id)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.get("/learning-summary")
async def get_learning_summary(
    time_period: str = Query("30d", description="时间周期: 7d, 30d, 90d"),
    current_user: User = Depends(get_current_user),
    learning_service: ProfileLearningService = Depends(get_learning_service),
    review_service: ProfileReviewService = Depends(get_review_service)
):
    """获取用户画像学习总结"""
    # 获取洞察报告
    insights = await learning_service.generate_profile_insights(current_user.id)
    
    # 获取回顾提醒
    quarterly_reminder = await review_service.generate_review_reminder(current_user.id, "quarterly")
    monthly_reminder = await review_service.generate_review_reminder(current_user.id, "monthly")
    
    # 构建总结
    summary = {
        "user_id": current_user.id,
        "time_period": time_period,
        "generated_at": datetime.now().isoformat(),
        "insights": insights.get("insights", []),
        "confidence_score": insights.get("confidence_score", 0),
        "recommendations": insights.get("recommendations", []),
        "review_reminders": {
            "quarterly": quarterly_reminder.get("reminder_content", {}),
            "monthly": monthly_reminder.get("reminder_content", {})
        },
        "learning_status": {
            "behavioral_learning_enabled": True,
            "contextual_learning_enabled": True,
            "interaction_analysis_enabled": True,
            "review_system_enabled": True
        }
    }
    
    return summary