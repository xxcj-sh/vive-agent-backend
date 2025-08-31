from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.schemas import BaseResponse
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("")
async def get_messages(
    matchId: str = Query(...),
    page: int = Query(1),
    limit: int = Query(20),
    current_user: User = Depends(get_current_user)
):
    """获取消息列表"""
    return BaseResponse(code=0, message="success", data=[])

@router.post("")
async def send_message(message_data: dict, current_user: User = Depends(get_current_user)):
    """发送消息"""
    return BaseResponse(code=0, message="success", data={"success": True})

@router.put("/read")
async def mark_messages_read(read_data: dict, current_user: User = Depends(get_current_user)):
    """标记消息已读"""
    return BaseResponse(code=0, message="success", data={"success": True})