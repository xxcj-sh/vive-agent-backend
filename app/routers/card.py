from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.db_config import get_db
from app.services.user_card_service import UserCardService
from app.models.user_card import CardCreate, CardUpdate
from app.dependencies import get_current_user
from typing import Dict, Any

router = APIRouter(
    prefix="/cards",
    tags=["cards"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{card_id}")
def get_card_details(
    card_id: str,
    db: Session = Depends(get_db)
):
    """通过card ID获取资料详情"""
    card = UserCardService.get_card_by_id(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # 获取完整的用户资料信息
    full_card = UserCardService.get_user_card_by_role(
        db, card.user_id, card.scene_type, card.role_type
    )
    
    if not full_card:
        raise HTTPException(status_code=404, detail="Card details not found")
    
    return {
        "code": 0,
        "message": "success",
        "data": full_card
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