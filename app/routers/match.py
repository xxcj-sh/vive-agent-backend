from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.schemas import BaseResponse
from app.utils.auth import get_current_user
from app.models.user import User
from app.services.match_card_strategy import match_card_strategy

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
    try:
        # 将 User 对象转换为字典格式
        current_user_dict = None
        if current_user:
            current_user_dict = {
                "id": getattr(current_user, 'id', None),
                "nickName": getattr(current_user, 'nick_name', None),
                "age": getattr(current_user, 'age', None),
                "interests": getattr(current_user, 'interests', []),
                "location": getattr(current_user, 'location', []),
                "preferences": getattr(current_user, 'preferences', {}),
            }
        
        # 使用匹配卡片策略服务
        result = match_card_strategy.get_match_cards(
            match_type=matchType,
            user_role=userRole,
            page=page,
            page_size=pageSize,
            current_user=current_user_dict
        )
        
        # 添加调试信息
        print(f"请求参数: matchType={matchType}, userRole={userRole}, page={page}, pageSize={pageSize}")
        print(f"当前用户: {current_user_dict}")
        print(f"策略返回结果: {result}")
        
        return BaseResponse(
            code=0, 
            message="success", 
            data=result
        )
    except Exception as e:
        print(f"获取匹配卡片异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取匹配卡片失败: {str(e)}",
            data=None
        )

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