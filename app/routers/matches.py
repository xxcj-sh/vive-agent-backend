import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.schemas import BaseResponse
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.enums import Gender
from app.models.enums import MatchActionType
from app.services.match_service.card_strategy import MatchCardStrategy
from app.services.match_service.core import MatchService
from app.services.user_card_service import UserCardService
from app.database import get_db
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import and_
from app.models.match_action import MatchAction
from app.models.enums import MatchActionType
from app.models.user_card_db import UserCard

router = APIRouter(prefix="/matches", tags=["匹配页面"])

# 请求模型
class MatchActionRequest(BaseModel):
    cardId: str
    action: str  # like, dislike, super_like, pass
    sceneType: Optional[str] = None  # housing, dating, activity
    sceneContext: Optional[str] = None

class SwipeRequest(BaseModel):
    cardId: str
    direction: str  # left, right, up, down
    sceneType: Optional[str] = None

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

@router.get("/cards")
async def get_match_cards(
    sceneType: Optional[str] = Query(None),
    userRole: Optional[str] = Query(None),
    page: int = Query(1),
    pageSize: int = Query(10),
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db)
):
    """获取匹配卡片"""
    try:
        print("current_user:", current_user)
        # 将 User 对象转换为字典格式
        current_user_dict = None
        if current_user:
            current_user_dict = {
                "id": current_user['id'],
                "nickName": current_user['nickName'],
                "gender": Gender(current_user.get('gender', 0)).name,
                "interests": getattr(current_user, 'interests', []),
                "location": getattr(current_user, 'location', []),
                "preferences": getattr(current_user, 'preferences', {}),
            }
        
        # 创建匹配卡片策略服务实例
        match_card_strategy = MatchCardStrategy(db_session)
        
        # 获取通用匹配卡片（不区分场景）
        result = match_card_strategy.get_universal_match_cards(
            page=page,
            page_size=pageSize,
            current_user=current_user_dict
        )

        
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
        result = await match_service.submit_match_action(
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
            "right": "collection",
            "left": "pass", 
            "up": "collection",
            "down": "pass"
        }
        
        action = direction_to_action.get(swipe_data.direction, "dislike")
        print("swipe direction:", swipe_data)
        # 构建操作数据
        action_data = MatchActionRequest(
            cardId=swipe_data.cardId,
            action=action
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

# 新增API：获取用户匹配操作历史
@router.get("/actions/history")
async def get_match_actions_history(
    sceneType: Optional[str] = Query(None),
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
            action_type=sceneType,
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

# 新增API：获取用户收到的匹配动作（用于trigger页面）
@router.get("/actions/received")
async def get_received_match_actions(
    actionType: Optional[str] = Query(None, description="动作类型，如 FOLLOW_AFTER_TRIGGER_IN_CHAT"),
    sceneType: Optional[str] = Query(None, description="场景类型"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户收到的匹配动作（用于trigger页面）"""
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 基础查询：获取用户收到的动作
        query = db.query(MatchAction).filter(
            MatchAction.target_user_id == user_id
        )
        
        # 如果指定了动作类型，添加筛选条件
        if actionType:
            query = query.filter(MatchAction.action_type == actionType)
        
        # 如果指定了场景类型，添加筛选条件
        if sceneType:
            query = query.filter(MatchAction.scene_type == sceneType)
        
        # 获取总数
        total = query.count()
        
        # 获取分页数据
        offset = (page - 1) * pageSize
        actions = query.order_by(MatchAction.created_at.desc()).offset(offset).limit(pageSize).all()
        
        # 获取操作用户的信息和卡片信息
        user_ids = [action.user_id for action in actions]
        card_ids = [action.target_card_id for action in actions]
        
        users = {str(user.id): user for user in db.query(User).filter(User.id.in_(user_ids)).all()}
        cards = {str(card.id): card for card in db.query(UserCard).filter(UserCard.id.in_(card_ids)).all()}
        
        # 格式化返回数据
        formatted_actions = []
        for action in actions:
            user = users.get(str(action.user_id))
            card = cards.get(str(action.target_card_id))
            
            if user and card:
                # 解析场景上下文
                scene_context = {}
                if action.scene_context:
                    try:
                        import json
                        scene_context = json.loads(action.scene_context) if action.scene_context else {}
                    except:
                        scene_context = {}
                
                formatted_action = {
                    "id": str(action.id),
                    "actionType": action.action_type.value,
                    "sceneType": action.scene_type,
                    "sceneContext": scene_context,
                    "createdAt": action.created_at.isoformat() if action.created_at else "",
                    "followerUser": {
                        "id": str(user.id),
                        "name": getattr(user, 'nick_name', None) or getattr(user, 'name', '匿名用户'),
                        "avatar": getattr(user, 'avatar_url', None) or "",
                        "age": getattr(user, 'age', 25),
                        "occupation": getattr(user, 'occupation', ''),
                        "location": getattr(user, 'location', ''),
                        "education": getattr(user, 'education', ''),
                        "bio": getattr(user, 'bio', ''),
                        "interests": getattr(user, 'interests', []) if isinstance(getattr(user, 'interests', []), list) else []
                    },
                    "cardInfo": {
                        "id": str(card.id),
                        "title": getattr(card, 'display_name', ''),
                        "sceneType": card.scene_type,
                        "roleType": card.role_type,
                        "bio": card.bio or '',
                        "location": getattr(card, 'location', '')
                    }
                }
                formatted_actions.append(formatted_action)
        
        return BaseResponse(
            code=0,
            message="success",
            data={
                "actions": formatted_actions,
                "total": total,
                "page": page,
                "pageSize": pageSize,
                "totalPages": (total + pageSize - 1) // pageSize
            }
        )
        
    except Exception as e:
        print(f"获取收到的匹配动作异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取收到的匹配动作失败: {str(e)}",
            data=None
        )

@router.get("/recommendation-cards")
async def get_match_recommendation_cards(
    sceneType: str = Query(None, description="匹配类型"),
    roleType: str = Query(None, description="用户角色"),
    status: str = Query(None, description="匹配状态"),
    page: int = Query(1, description="页码"),
    pageSize: int = Query(10, description="每页数量"),
    limit: int = Query(None, description="每页数量(兼容参数)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取匹配推荐列表
    
    统一使用 /api/v1/matches/recommendation-cards 端点
    """

    try:
        # 直接从user_cards表获取所有非用户本人创建的卡片
        from sqlalchemy import and_, or_
        from app.models.user import User
        from app.models.user_card_db import UserCard
        
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        print(f"=== 获取匹配推荐 - 调试信息 ===")
        print(f"当前用户ID: {user_id}")
        print(f"场景类型: {sceneType}")
        print(f"用户角色: {roleType}")
        print(f"分页: page={page}, pageSize={pageSize}")
        
        # 从user_cards表查询所有非当前用户创建的活跃卡片
        print("正在查询用户卡片...")
        
        # 基础查询：获取所有活跃的、非当前用户创建的卡片
        card_query = db.query(UserCard).filter(
            and_(
                UserCard.is_active == 1,
                UserCard.user_id != user_id  # 排除用户自己创建的卡片
            )
        )
    
        
        # 获取总数
        total_cards = card_query.count()
        print(f"符合条件的卡片总数: {total_cards}")
        
        # 分页获取卡片
        offset = (page - 1) * pageSize
        user_cards = card_query.order_by(UserCard.created_at.desc()).offset(offset).limit(pageSize).all()
        print(f"当前页获取卡片数量: {len(user_cards)}")
        
        # 构建返回数据
        cards = []
        print("开始处理卡片数据...")
        
        for i, user_card in enumerate(user_cards):
            print(f"处理第{i+1}个卡片: card_id={user_card.id}, user_id={user_card.user_id}")
            
            # 获取卡片创建者信息
            card_creator = db.query(User).filter(User.id == str(user_card.user_id)).first()
            if not card_creator:
                print(f"跳过: 找不到卡片创建者 user_id={user_card.user_id}")
                continue
            
            # 构建卡片数据
            card_data = {
                "id": str(user_card.id),
                "userId": str(card_creator.id),
                "sceneType": user_card.scene_type or sceneType,
                "userRole": roleType,
                "creatorName": getattr(user_card, 'display_name', None) or getattr(card_creator, 'name', '匿名用户'),
                "avatar": getattr(user_card, 'avatar_url', None) or "",
                "creatorAvatar": getattr(card_creator, 'avatar_url', None) or "",
                "creatorAge": getattr(card_creator, 'age', 25),
                "creatorOccupation": getattr(card_creator, 'occupation', ''),
                "location": getattr(user_card, 'location', ''),
                "bio": getattr(user_card, 'bio', ''),
                "creatorInterests": getattr(card_creator, 'interests', []) if isinstance(getattr(card_creator, 'interests', []), list) else [],
                "createdAt": user_card.created_at.isoformat() if user_card.created_at else "",
                "recommendReason": '系统推荐',
                "cardTitle": str(user_card.display_name),
                "displayName": getattr(user_card, 'display_name', None)
            }
            
            cards.append(card_data)
        
        print(f"成功处理卡片数量: {len(cards)}")
        
        return BaseResponse(
            code=0,
            message="success",
            data={
                "cards": cards,
                "pagination": {
                    "page": page,
                    "pageSize": pageSize,
                    "total": total_cards,
                    "totalPages": (total_cards + pageSize - 1) // pageSize
                },
                "source": "user_cards"
            }
        )
            
    except Exception as e:
        print(f"获取匹配推荐异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取匹配推荐失败: {str(e)}",
            data=None
        )


# 收藏卡片相关API
@router.post("/collect")
async def collect_card(
    card_id: str = Query(..., description="卡片ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """收藏卡片"""
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 创建匹配服务实例
        match_service = MatchService(db)
        print("收藏动作", user_id, card_id)
        # 提交收藏操作
        result = match_service.submit_match_action(
            user_id=user_id,
            action_data={
                "cardId": card_id,
                "action": MatchActionType.COLLECTION.value,
                "source": "user"
            }
        )
        
        return BaseResponse(
            code=0,
            message="收藏成功",
            data=result
        )
        
    except ValueError as e:
        return BaseResponse(
            code=400,
            message=str(e),
            data=None
        )
    except Exception as e:
        print(f"收藏卡片异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"收藏卡片失败: {str(e)}",
            data=None
        )

@router.get("/collected")
async def get_collected_cards(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户收藏的卡片列表"""
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 创建匹配服务实例
        match_service = MatchService(db)
        
        # 获取收藏的卡片
        result = match_service.get_collected_cards(
            user_id=user_id,
            page=page,
            page_size=pageSize
        )
        
        return BaseResponse(
            code=0,
            message="success",
            data=result
        )
        
    except Exception as e:
        print(f"获取收藏卡片列表异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取收藏卡片列表失败: {str(e)}",
            data=None
        )

@router.delete("/collect/{card_id}")
async def cancel_collect_card(
    card_id: str,
    scene_type: str = Query(..., description="场景类型"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消收藏卡片"""
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 创建匹配服务实例
        match_service = MatchService(db)
        
        # 取消收藏
        result = match_service.cancel_collect_card(
            user_id=user_id,
            card_id=card_id,
            scene_type=scene_type
        )
        
        return BaseResponse(
            code=0,
            message="取消收藏成功",
            data=result
        )
        
    except Exception as e:
        print(f"取消收藏卡片异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"取消收藏卡片失败: {str(e)}",
            data=None
        )

@router.get("/{match_id}")
async def get_match_detail(
    match_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取匹配详情
    
    根据匹配ID获取单个匹配的详细信息
    """
    print("=== Match Detail API Called ===")
    print(f"URL: /api/v1/matches/{match_id}")
    print(f"Match ID: {match_id}")
    
    try:
        match_service = MatchService(db)
        
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 获取匹配详情
        match_detail = match_service.get_match_detail(
            match_id=match_id,
            user_id=user_id
        )
        
        if not match_detail:
            return BaseResponse(
                code=404,
                message="匹配记录不存在",
                data=None
            )
        
        return BaseResponse(
            code=0,
            message="success",
            data=match_detail
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