"""
用户画像API路由（增强版）
提供用户画像数据的CRUD操作、分析接口和智能功能
整合了基础功能和增强功能，避免重复
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.services.user_profile_service import UserProfileService
from app.services.enhanced_user_profile_service import EnhancedUserProfileService
from app.models.user_profile import (
    UserProfileCreate, 
    UserProfileUpdate, 
    UserProfileResponse,
    UserProfileListResponse,
    UserProfileAnalysisRequest,
    UserProfileAnalysisResponse
)
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/profiles", tags=["user-profiles"])


def get_enhanced_profile_service(db: Session = Depends(get_db)) -> EnhancedUserProfileService:
    """获取增强用户画像服务实例"""
    return EnhancedUserProfileService(db)


@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建用户画像（增强版）
    支持当前用户或管理员创建
    """
    service = UserProfileService(db)
    try:
        # 如果profile_data中没有user_id，使用当前用户ID
        if not profile_data.user_id:
            profile_data.user_id = str(current_user.id)
        
        # 权限检查：用户只能创建自己的画像，管理员可以创建任何用户的画像
        if profile_data.user_id != str(current_user.id) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="权限不足，只能创建自己的用户画像")
        
        profile = service.create_user_profile(profile_data)
        return UserProfileResponse.from_orm(profile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建用户画像失败: {str(e)}")


@router.get("/{profile_id}", response_model=UserProfileResponse)
async def get_user_profile(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """
    获取用户画像详情
    """
    service = UserProfileService(db)
    profile = service.get_user_profile(profile_id)
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户画像不存在")
    
    return UserProfileResponse.from_orm(profile)


@router.get("/user/{user_id}/active", response_model=UserProfileResponse)
async def get_active_user_profile(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的激活画像（增强版）
    添加权限控制，用户只能查看自己的画像，管理员可以查看所有用户的画像
    """
    # 权限检查
    if str(current_user.id) != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足，只能查看自己的用户画像")
    
    service = UserProfileService(db)
    profile = service.get_active_user_profile(user_id)
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户没有激活的画像")
    
    return UserProfileResponse.from_orm(profile)


@router.get("/user/{user_id}/all", response_model=UserProfileListResponse)
async def get_user_profiles(
    user_id: str,
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """
    获取用户的所有画像
    """
    service = UserProfileService(db)
    profiles = service.get_user_profiles(user_id, include_inactive)
    
    return UserProfileListResponse(
        profiles=[UserProfileResponse.from_orm(profile) for profile in profiles],
        total_count=len(profiles),
        active_count=len([p for p in profiles if p.is_active == 1])
    )


@router.put("/{profile_id}", response_model=UserProfileResponse)
async def update_user_profile(
    profile_id: str,
    update_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    更新用户画像
    """
    service = UserProfileService(db)
    profile = service.update_user_profile(profile_id, update_data)
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户画像不存在")
    
    return UserProfileResponse.from_orm(profile)


@router.post("/{profile_id}/activate", response_model=UserProfileResponse)
async def activate_user_profile(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """
    激活用户画像
    """
    service = UserProfileService(db)
    success = service.activate_user_profile(profile_id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户画像不存在")
    
    profile = service.get_user_profile(profile_id)
    return UserProfileResponse.from_orm(profile)


@router.post("/{profile_id}/deactivate", response_model=UserProfileResponse)
async def deactivate_user_profile(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """
    停用用户画像
    """
    service = UserProfileService(db)
    success = service.deactivate_user_profile(profile_id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户画像不存在")
    
    profile = service.get_user_profile(profile_id)
    return UserProfileResponse.from_orm(profile)


@router.post("/analyze/preferences", response_model=UserProfileAnalysisResponse)
async def analyze_user_preferences(
    request: UserProfileAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    分析用户偏好
    """
    service = UserProfileService(db)
    result = service.analyze_user_preferences(request.user_id)
    
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    
    return UserProfileAnalysisResponse(
        user_id=result["user_id"],
        analysis_type=result["analysis_type"],
        results={
            "preferences": result["preferences"],
            "interest_tags": result["interest_tags"],
            "social_preferences": result["social_preferences"],
            "match_preferences": result["match_preferences"]
        },
        confidence_score=result["confidence_score"],
        data_source=result["data_source"],
        generated_at=result["generated_at"]
    )


@router.post("/analyze/personality", response_model=UserProfileAnalysisResponse)
async def analyze_user_personality(
    request: UserProfileAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    分析用户个性
    """
    service = UserProfileService(db)
    result = service.analyze_user_personality(request.user_id)
    
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    
    return UserProfileAnalysisResponse(
        user_id=result["user_id"],
        analysis_type=result["analysis_type"],
        results={
            "personality_traits": result["personality_traits"],
            "behavior_patterns": result["behavior_patterns"]
        },
        confidence_score=result["confidence_score"],
        data_source=result["data_source"],
        generated_at=result["generated_at"]
    )


@router.post("/analyze/mood", response_model=UserProfileAnalysisResponse)
async def analyze_user_mood(
    request: UserProfileAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    分析用户心情
    """
    service = UserProfileService(db)
    result = service.analyze_user_mood(request.user_id)
    
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    
    return UserProfileAnalysisResponse(
        user_id=result["user_id"],
        analysis_type=result["analysis_type"],
        results={
            "mood_state": result["mood_state"]
        },
        confidence_score=result["confidence_score"],
        data_source=result["data_source"],
        generated_at=result["generated_at"]
    )


@router.get("/user/{user_id}/statistics")
async def get_profile_statistics(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户画像统计信息（增强版）
    添加权限控制
    """
    # 权限检查
    if str(current_user.id) != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足，只能查看自己的统计信息")
    
    service = UserProfileService(db)
    statistics = service.get_profile_statistics(user_id)
    
    return statistics


# ===== 增强功能接口（原user_profile_enhanced.py的核心功能） =====

@router.post("/smart-update")
async def update_with_smart_suggestions(
    update_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    service: EnhancedUserProfileService = Depends(get_enhanced_profile_service)
):
    """
    智能更新用户画像（基于AI建议）
    整合自user_profile_enhanced.py的增强功能
    """
    result = await service.update_with_smart_suggestions(current_user.id, update_data)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/implicit-learning")
async def perform_implicit_learning(
    interaction_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    service: EnhancedUserProfileService = Depends(get_enhanced_profile_service)
):
    """
    执行隐式学习更新
    根据用户交互行为自动更新画像
    """
    result = await service.perform_implicit_learning(current_user.id, interaction_data)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/periodic-review")
async def perform_periodic_review(
    review_type: str = Query("monthly", description="回顾类型: monthly, quarterly"),
    current_user: User = Depends(get_current_user),
    service: EnhancedUserProfileService = Depends(get_enhanced_profile_service)
):
    """
    执行定期回顾
    定期分析和优化用户画像
    """
    result = await service.perform_periodic_review(current_user.id, review_type)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/recommendations")
async def get_smart_recommendations(
    recommendation_type: str = Query("all", description="推荐类型: all, content, social, activity"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: EnhancedUserProfileService = Depends(get_enhanced_profile_service)
):
    """
    获取智能推荐
    基于用户画像提供个性化推荐
    """
    result = await service.get_smart_recommendations(current_user.id, recommendation_type, limit)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/me/enhanced")
async def get_my_enhanced_profile(
    include_history: bool = Query(False, description="是否包含历史记录"),
    include_recommendations: bool = Query(False, description="是否包含推荐"),
    current_user: User = Depends(get_current_user),
    service: EnhancedUserProfileService = Depends(get_enhanced_profile_service)
):
    """
    获取当前用户的增强画像
    包含更多智能分析结果
    """
    result = await service.get_user_profile(current_user.id, include_history)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # 如果需要推荐，添加推荐数据
    if include_recommendations:
        recommendations = await service.get_smart_recommendations(current_user.id, "all", 5)
        result["recommendations"] = recommendations
    
    return result


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {
        "status": "healthy",
        "service": "user_profile_enhanced",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "基础CRUD操作",
            "智能分析",
            "隐式学习",
            "定期回顾",
            "智能推荐"
        ]
    }