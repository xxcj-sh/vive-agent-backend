from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import BaseResponse
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/{property_id}")
async def get_property_detail(property_id: str, current_user: User = Depends(get_current_user)):
    """获取房源详情"""
    return BaseResponse(code=0, message="success", data={"id": property_id})