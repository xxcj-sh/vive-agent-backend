"""
用户画像API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user_profile import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
    UserProfileListResponse
)
from app.models.user_profile_history import UserProfileHistoryListResponse
from app.services.user_profile import UserProfileService

router = APIRouter(prefix="/profiles", tags=["用户画像"])


def get_service(db: Session = Depends(get_db)) -> UserProfileService:
    """获取服务实例"""
    return UserProfileService(db)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    service: UserProfileService = Depends(get_service)
):
    """获取用户画像（不存在时自动创建）"""
    try:
        return service.get_or_create_profile(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户画像失败: {str(e)}"
        )


@router.post("/{user_id}", response_model=UserProfileResponse)
async def create_user_profile(
    user_id: str,
    profile: UserProfileCreate,
    service: UserProfileService = Depends(get_service)
):
    """创建用户画像"""
    try:
        # 检查是否已存在
        existing_profile = service.get_user_profile(user_id)
        if existing_profile and existing_profile.raw_profile is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户画像已存在"
            )
        
        # 创建新画像
        profile_data = UserProfileCreate(
            user_id=user_id,
            raw_profile=profile.raw_profile,
            update_reason=profile.update_reason or "初始创建"
        )
        return service.create_user_profile(profile_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户画像失败: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: str,
    profile_update: UserProfileUpdate,
    service: UserProfileService = Depends(get_service)
):
    """更新用户画像"""
    try:
        return await service.update_profile(user_id, profile_update, change_source="user")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户画像失败: {str(e)}"
        )


@router.get("/{user_id}/history", response_model=UserProfileHistoryListResponse)
async def get_user_profile_history(
    user_id: str,
    limit: Optional[int] = 50,
    service: UserProfileService = Depends(get_service)
):
    """获取用户画像历史记录"""
    try:
        history_list = service.get_profile_history(user_id, limit)
        return UserProfileHistoryListResponse(
            history=history_list,
            total_count=len(history_list),
            user_id=user_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取历史记录失败: {str(e)}"
        )


@router.post("/{user_id}/validate")
async def validate_raw_profile(
    user_id: str,
    raw_profile: str,
    service: UserProfileService = Depends(get_service)
):
    """验证原始画像数据格式"""
    try:
        is_valid = service.validate_raw_profile(raw_profile)
        parsed_data = service.parse_raw_profile(raw_profile) if is_valid else None
        
        return {
            "is_valid": is_valid,
            "parsed_data": parsed_data,
            "error": None if is_valid else "Invalid JSON format"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证失败: {str(e)}"
        )