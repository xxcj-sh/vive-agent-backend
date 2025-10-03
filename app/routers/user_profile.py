"""
用户画像API路由
提供用户画像数据的CRUD操作和分析接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.services.user_profile_service import UserProfileService
from app.models.user_profile import (
    UserProfileCreate, 
    UserProfileUpdate, 
    UserProfileResponse,
    UserProfileListResponse,
    UserProfileAnalysisRequest,
    UserProfileAnalysisResponse
)

router = APIRouter(prefix="/user-profiles", tags=["user-profiles"])


@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    profile_data: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """
    创建用户画像
    """
    service = UserProfileService(db)
    try:
        profile = service.create_user_profile(profile_data)
        return UserProfileResponse.from_orm(profile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建用户画像失败")


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
    db: Session = Depends(get_db)
):
    """
    获取用户的激活画像
    """
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
    db: Session = Depends(get_db)
):
    """
    获取用户画像统计信息
    """
    service = UserProfileService(db)
    statistics = service.get_profile_statistics(user_id)
    
    return statistics