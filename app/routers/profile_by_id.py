from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.db_config import get_db
from app.services.user_card_service import UserCardService

router = APIRouter(
    prefix="/cards",
    tags=["cards"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{card_id}/details")
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