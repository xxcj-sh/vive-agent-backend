from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.db_config import get_db
from app.services.user_card_service import UserCardService
from app.models.user_card import CardCreate, CardUpdate
from app.dependencies import get_current_user
from typing import Dict, Any, Optional

router = APIRouter(
    prefix="/cards",
    tags=["cards"],
    responses={404: {"description": "Not found"}},
)


@router.get("/public")
def get_public_cards(
    page: int = 1,
    page_size: int = 10,
    scene_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取公开卡片列表"""
    try:
        # 验证页码和每页数量
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 10
            
        # 调用服务获取公开卡片列表
        result = UserCardService.get_public_cards(db, page, page_size, scene_type)
        
        return {
            "code": 0,
            "message": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取公开卡片列表失败: {str(e)}")


@router.get("/{card_id}")
def get_card_details(
    card_id: str,
    db: Session = Depends(get_db)
):
    """通过card ID获取资料详情，包含卡片信息和用户基础资料"""
    from app.models.user import User
    
    card = UserCardService.get_card_by_id(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # 获取用户基础信息
    user = db.query(User).filter(User.id == card.user_id).first()
    
    # 构建响应数据，包含卡片信息和用户基础资料
    response_data = {
        "id": card.id,
        "user_id": card.user_id,
        "role_type": card.role_type,
        "scene_type": card.scene_type,
        "display_name": card.display_name,
        "avatar_url": card.avatar_url,
        "bio": card.bio,
        "trigger_and_output": card.trigger_and_output or {},
        "profile_data": card.profile_data or {},
        "preferences": card.preferences or {},
        "visibility": card.visibility,
        "created_at": card.created_at,
        "updated_at": card.updated_at,
        # 用户基础信息
        "user_info": {
            "nick_name": user.nick_name if user else None,
            "age": user.age if user else None,
            "gender": user.gender if user else None,
            "occupation": getattr(user, 'occupation', None) if user else None,
            "location": getattr(user, 'location', None) if user else None,
            "education": getattr(user, 'education', None) if user else None,
            "interests": getattr(user, 'interests', []) if user else [],
            "avatar_url": user.avatar_url if user else None
        } if user else None
    }
    
    return {
        "code": 0,
        "message": "success",
        "data": response_data
    }

@router.post("")
def create_card(
    card_data: CardCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新的用户角色卡片"""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
            
        new_card = UserCardService.create_card(db, user_id, card_data)
        return {
            "code": 0,
            "message": "success",
            "data": {
                "id": new_card.id,
                "user_id": new_card.user_id,
                "role_type": new_card.role_type,
                "scene_type": new_card.scene_type,
                "display_name": new_card.display_name,
                "avatar_url": new_card.avatar_url,
                "bio": new_card.bio,
                "trigger_and_output": new_card.trigger_and_output or {},
                "profile_data": new_card.profile_data or {},
                "preferences": new_card.preferences or {},
                "visibility": new_card.visibility,
                "created_at": new_card.created_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{card_id}")
def update_card(
    card_id: str,
    card_data: CardUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户角色卡片"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    # 首先检查卡片是否存在且属于当前用户
    existing_card = UserCardService.get_card_by_id(db, card_id)
    if not existing_card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    if existing_card.user_id != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 执行更新
    updated_card = UserCardService.update_card(db, card_id, card_data.dict(exclude_unset=True))
    if not updated_card:
        raise HTTPException(status_code=404, detail="Failed to update card")
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": updated_card.id,
            "user_id": updated_card.user_id,
            "role_type": updated_card.role_type,
            "scene_type": updated_card.scene_type,
            "display_name": updated_card.display_name,
            "avatar_url": updated_card.avatar_url,
            "bio": updated_card.bio,
            "trigger_and_output": updated_card.trigger_and_output or {},
            "profile_data": updated_card.profile_data or {},
            "preferences": updated_card.preferences or {},
            "visibility": updated_card.visibility,
            "updated_at": updated_card.updated_at
        }
    }


@router.delete("/{card_id}")
def delete_card(
    card_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户角色卡片（软删除）"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    # 首先检查卡片是否存在且属于当前用户
    existing_card = UserCardService.get_card_by_id(db, card_id)
    if not existing_card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    if existing_card.user_id != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 执行软删除
    success = UserCardService.delete_card(db, card_id)
    if not success:
        raise HTTPException(status_code=404, detail="Failed to delete card")
    
    return {
        "code": 0,
        "message": "success",
        "data": {"deleted": True}
    }


@router.post("/{card_id}/anonymous")
def toggle_anonymous_mode(
    card_id: str,
    enable_anonymous: bool,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换卡片的匿名模式"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    # 检查卡片是否存在且属于当前用户
    existing_card = UserCardService.get_card_by_id(db, card_id)
    if not existing_card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    if existing_card.user_id != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 切换匿名模式
    from app.models.user_card_db import VISIBILITY_ANONYMOUS, VISIBILITY_PUBLIC
    new_visibility = VISIBILITY_ANONYMOUS if enable_anonymous else VISIBILITY_PUBLIC
    
    updated_card = UserCardService.update_card(db, card_id, {"visibility": new_visibility})
    if not updated_card:
        raise HTTPException(status_code=404, detail="Failed to update card")
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": updated_card.id,
            "visibility": updated_card.visibility,
            "anonymous_mode": updated_card.visibility == VISIBILITY_ANONYMOUS
        }
    }


@router.get("/{card_id}/anonymous/status")
def get_anonymous_status(
    card_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取卡片的匿名模式状态"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    # 检查卡片是否存在且属于当前用户
    existing_card = UserCardService.get_card_by_id(db, card_id)
    if not existing_card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    if existing_card.user_id != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    from app.models.user_card_db import VISIBILITY_ANONYMOUS
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": existing_card.id,
            "visibility": existing_card.visibility,
            "anonymous_mode": existing_card.visibility == VISIBILITY_ANONYMOUS
        }
    }