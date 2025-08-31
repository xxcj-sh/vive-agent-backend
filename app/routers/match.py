from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.schemas import BaseResponse
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/cards")
async def get_match_cards(
    matchType: str = Query(...),
    userRole: str = Query(...),
    page: int = Query(1),
    pageSize: int = Query(10),
    current_user: User = Depends(get_current_user)
):
    """获取匹配卡片"""
    return BaseResponse(code=0, message="success", data=[])

@router.post("/actions")
async def create_match_action(action_data: dict, current_user: User = Depends(get_current_user)):
    """创建匹配操作"""
    return BaseResponse(code=0, message="success", data={"success": True})

@router.post("/swipes")
async def swipe_card(swipe_data: dict, current_user: User = Depends(get_current_user)):
    """滑动卡片"""
    return BaseResponse(code=0, message="success", data={"success": True})

@router.get("")
async def get_matches(
    status: str = Query("all"),
    page: int = Query(1),
    pageSize: int = Query(10),
    current_user: User = Depends(get_current_user)
):
    """获取匹配列表"""
    return BaseResponse(code=0, message="success", data=[])

@router.get("/{match_id}")
async def get_match_detail(match_id: str, current_user: User = Depends(get_current_user)):
    """获取匹配详情"""
    return BaseResponse(code=0, message="success", data={"id": match_id})