from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.schemas import BaseResponse
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.enums import Gender
from app.services.match_card_strategy import match_card_strategy
from app.services.match_service_simple import MatchService
from app.database import get_db
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# 请求模型
class MatchActionRequest(BaseModel):
    cardId: str
    action: str  # like, dislike, super_like, pass
    matchType: str  # housing, dating, activity
    sceneContext: Optional[str] = None

class SwipeRequest(BaseModel):
    cardId: str
    direction: str  # left, right, up, down
    matchType: Optional[str] = None

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
        print("current_user:", current_user)
        # 将 User 对象转换为字典格式
        current_user_dict = None
        print("getattr(current_user, 'id'):", current_user['id'])
        if current_user:
            current_user_dict = {
                "id": current_user['id'],
                "nickName": current_user['nickName'],
                "gender": Gender(current_user.get('gender', 0)).name,
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
async def create_match_action(
    action_data: MatchActionRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交匹配操作"""
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 创建匹配服务实例
        match_service = MatchService(db)
        
        # 提交匹配操作
        result = match_service.submit_match_action(
            user_id=user_id,
            action_data=action_data.dict()
        )
        
        return BaseResponse(
            code=0,
            message="success",
            data=result
        )
        
    except ValueError as e:
        return BaseResponse(
            code=400,
            message=str(e),
            data=None
        )
    except Exception as e:
        print(f"匹配操作异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"匹配操作失败: {str(e)}",
            data=None
        )

@router.post("/swipes")
async def swipe_card(
    swipe_data: SwipeRequest, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """滑动卡片"""
    try:
        # 将滑动方向转换为匹配操作
        direction_to_action = {
            "right": "like",
            "left": "dislike", 
            "up": "super_like",
            "down": "pass"
        }
        
        action = direction_to_action.get(swipe_data.direction, "dislike")
        
        # 构建操作数据
        action_data = MatchActionRequest(
            cardId=swipe_data.cardId,
            action=action,
            matchType=swipe_data.matchType or "dating"
        )
        
        # 复用匹配操作逻辑
        return await create_match_action(action_data, current_user, db)
        
    except Exception as e:
        print(f"滑动卡片异常: {str(e)}")
        return BaseResponse(
            code=500,
            message=f"滑动操作失败: {str(e)}",
            data=None
        )

@router.get("")
async def get_matches(
    status: str = Query("all"),
    page: int = Query(1),
    pageSize: int = Query(10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取匹配列表"""
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 创建匹配服务实例
        match_service = MatchService(db)
        
        # 获取匹配列表
        result = match_service.get_user_matches(
            user_id=user_id,
            status=status,
            page=page,
            page_size=pageSize
        )
        
        return BaseResponse(
            code=0,
            message="success",
            data=result
        )
        
    except Exception as e:
        print(f"获取匹配列表异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取匹配列表失败: {str(e)}",
            data=None
        )

@router.get("/{match_id}")
async def get_match_detail(
    match_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取匹配详情"""
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 创建匹配服务实例
        match_service = MatchService(db)
        
        # 获取匹配详情
        result = match_service.get_match_detail(match_id, user_id)
        
        if not result:
            return BaseResponse(
                code=404,
                message="匹配记录不存在",
                data=None
            )
        
        return BaseResponse(
            code=0,
            message="success",
            data=result
        )
        
    except Exception as e:
        print(f"获取匹配详情异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取匹配详情失败: {str(e)}",
            data=None
        )

# 新增API：获取用户匹配操作历史
@router.get("/actions/history")
async def get_match_actions_history(
    matchType: Optional[str] = Query(None),
    page: int = Query(1),
    pageSize: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户匹配操作历史"""
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 创建匹配服务实例
        match_service = MatchService(db)
        
        # 获取操作历史
        result = match_service.get_user_match_actions(
            user_id=user_id,
            match_type=matchType,
            page=page,
            page_size=pageSize
        )
        
        return BaseResponse(
            code=0,
            message="success",
            data=result
        )
        
    except Exception as e:
        print(f"获取操作历史异常: {str(e)}")
        return BaseResponse(
            code=500,
            message=f"获取操作历史失败: {str(e)}",
            data=None
        )