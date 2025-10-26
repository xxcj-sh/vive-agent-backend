"""
用户画像智能学习API路由
提供用户画像的智能分析、学习、洞察生成等功能
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.services.user_profile_learning_service import ProfileLearningService
from app.services.user_profile_review_service import ProfileReviewService
from app.utils.auth import get_current_user
from app.models.user import User
from datetime import datetime

logger = logging.getLogger(__name__)

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
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ProfileLearningService = Depends(get_learning_service)
):
    """分析用户交互行为"""
    # 验证交互数据
    if not interaction_data or "type" not in interaction_data:
        raise HTTPException(status_code=400, detail="交互数据格式错误")
    
    # 分析交互
    result = await service.analyze_user_interaction(current_user["id"], interaction_data)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/behavioral-learning")
async def perform_behavioral_learning(
    time_window: str = Query("30d", description="时间窗口: 7d, 30d, 90d"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ProfileLearningService = Depends(get_learning_service)
):
    """基于用户行为模式进行学习"""
    # 执行行为学习
    result = await service.perform_behavioral_learning(current_user["id"], time_window)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/contextual-learning")
async def perform_contextual_learning(
    context_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ProfileLearningService = Depends(get_learning_service)
):
    """基于上下文信息进行学习"""
    # 验证上下文数据
    if not context_data or "type" not in context_data:
        raise HTTPException(status_code=400, detail="上下文数据格式错误")
    
    # 执行上下文学习
    result = await service.perform_contextual_learning(current_user["id"], context_data)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.get("/generate-insights")
async def generate_profile_insights(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ProfileLearningService = Depends(get_learning_service)
):
    """生成用户画像洞察报告"""
    # 生成洞察
    result = await service.generate_profile_insights(current_user["id"])
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


from pydantic import BaseModel, Field

class InitializeProfileRequest(BaseModel):
    """初始化用户画像请求"""
    nickname: str = Field(..., description="用户昵称")
    gender: str = Field(..., description="用户性别")
    age: Optional[int] = Field(None, description="用户年龄")
    location: Optional[str] = Field(None, description="用户地区")
    bio: Optional[str] = Field(None, description="个人简介")
    birthday: Optional[str] = Field(None, description="生日")


@router.post("/initialize-profile")
async def initialize_profile(
    request: InitializeProfileRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: ProfileLearningService = Depends(get_learning_service)
):
    """基于用户基本资料初始化用户画像"""
    try:
        # 构建基本资料数据
        basic_data = {
            "nickname": request.nickname,
            "gender": request.gender,
            "age": request.age,
            "location": request.location,
            "bio": request.bio,
            "birthday": request.birthday
        }
        
        # 调用画像初始化服务 - current_user是字典，使用id字段
        result = await service.initialize_user_profile(current_user["id"], basic_data)
        
        if "error" in result:
            return {
                "code": 400,
                "message": result["error"],
                "data": None
            }
        
        return {
            "code": 200,
            "message": "用户画像初始化成功",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"用户画像初始化失败: {str(e)}")
        return {
            "code": 500,
            "message": f"用户画像初始化失败: {str(e)}",
            "data": None
        }

