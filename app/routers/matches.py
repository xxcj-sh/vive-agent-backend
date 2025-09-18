import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.schemas import BaseResponse
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.enums import Gender
from app.services.match_service.models import MatchActionType
from app.services.match_service.card_strategy import MatchCardStrategy
from app.services.match_service.core import MatchService
from app.database import get_db
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/matches", tags=["匹配页面"])

# 请求模型
class MatchActionRequest(BaseModel):
    cardId: str
    action: str  # like, dislike, super_like, pass
    sceneType: str  # housing, dating, activity
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
        
        # 如果 sceneType 或 userRole 参数不可用，返回不区分场景的通用卡片
        if not sceneType or not userRole:
            # 获取通用匹配卡片（不区分场景）
            result = match_card_strategy.get_universal_match_cards(
                page=page,
                page_size=pageSize,
                current_user=current_user_dict
            )
        else:
            # 使用匹配卡片策略服务
            result = match_card_strategy.get_match_cards(
                scene_type=sceneType,
                role_type=userRole,
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
            sceneType=swipe_data.sceneType or "dating"
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
        # 优先获取AI推荐
        from sqlalchemy import and_
        from app.models.match_action import MatchAction, MatchActionType
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
        
        # 先尝试获取AI推荐
        print("正在查询AI推荐...")
        ai_recommend_actions = db.query(MatchAction).filter(
            and_(
                MatchAction.target_user_id == user_id,
                MatchAction.action_type == MatchActionType.AI_RECOMMEND_AFTER_USER_CHAT
            )
        ).order_by(MatchAction.created_at.desc())
        
        # 打印查询SQL
        print(f"AI推荐查询SQL: {str(ai_recommend_actions.statement)}")
        
        ai_total = ai_recommend_actions.count()
        print(f"AI推荐总数: {ai_total}")
        
        ai_actions = ai_recommend_actions.offset((page - 1) * pageSize).limit(pageSize).all()
        print(f"当前页AI推荐数量: {len(ai_actions)}")
        
        if ai_total > 0:
            # 有AI推荐，返回AI推荐数据
            cards = []
            print("开始处理AI推荐数据...")
            for i, action in enumerate(ai_actions):
                print(f"处理第{i+1}个AI推荐: action_id={action.id}, user_id={action.user_id}")
                
                target_user = db.query(User).filter(User.id == str(action.user_id)).first()
                if not target_user:
                    print(f"跳过: 找不到目标用户 user_id={action.user_id}")
                    continue
                    
                target_card = db.query(UserCard).filter(
                    UserCard.user_id == str(action.user_id),
                    UserCard.is_active == 1
                ).first()
                
                if not target_card:
                    print(f"跳过: 找不到目标卡片 user_id={action.user_id}, scene_type={sceneType}")
                    continue
                
                scene_context = {}
                if action.scene_context:
                    try:
                        scene_context = json.loads(action.scene_context)
                    except:
                        pass
                
                card_data = {
                    "id": str(action.id),
                    "userId": str(target_user.id),
                    "sceneType": sceneType,
                    "userRole": roleType,
                    "name": getattr(target_user, 'nick_name', None) or getattr(target_user, 'name', '匿名用户'),
                    "avatar": getattr(target_user, 'avatar_url', None) or "",
                    "age": getattr(target_user, 'age', 25),
                    "occupation": getattr(target_user, 'occupation', ''),
                    "location": getattr(target_user, 'location', ''),
                    "bio": getattr(target_user, 'bio', ''),
                    "interests": getattr(target_user, 'interests', []) if isinstance(getattr(target_user, 'interests', []), list) else [],
                    "createdAt": action.created_at.isoformat() if action.created_at else "",
                    "matchScore": scene_context.get('aiAnalysis', {}).get('matchScore', 85),
                    "recommendReason": scene_context.get('aiAnalysis', {}).get('preferenceJudgement', '基于聊天内容智能推荐')
                }
                
                # 场景特定字段
                if sceneType == "activity":
                    card_data.update({
                        "activityName": getattr(target_card, 'title', ''),
                        "activityTime": getattr(target_card, 'activity_time', ''),
                        "activityLocation": getattr(target_card, 'location', ''),
                        "activityPrice": getattr(target_card, 'price', 0),
                        "activityType": getattr(target_card, 'activity_type', '')
                    })
                
                cards.append(card_data)
            
            return BaseResponse(
                code=0,
                message="success",
                data={
                    "cards": cards,
                    "pagination": {
                        "page": page,
                        "pageSize": pageSize,
                        "total": ai_total,
                        "totalPages": (ai_total + pageSize - 1) // pageSize
                    },
                    "source": "ai_recommendations"
                }
            )
        else:
            # 没有AI推荐，使用普通匹配推荐
            print("没有AI推荐，使用普通匹配推荐")
            from app.services.match_service import MatchService
            match_service = MatchService(db)
            
            # 获取匹配卡片
            print(f"调用普通推荐服务: user_id={user_id}, scene_type={sceneType}, role_type={roleType}")
            cards_data = match_service.get_recommendation_cards(
                user_id=user_id,
                scene_type=sceneType,
                role_type=roleType,
                page=page,
                page_size=pageSize
            )
            
            total_cards = cards_data.get("total", 0)
            cards_list = cards_data.get("cards", [])
            print(f"普通推荐结果: 总数={total_cards}, 当前页数量={len(cards_list)}")
            
            return BaseResponse(
                code=0,
                message="success",
                data={
                    "cards": cards_list,
                    "pagination": {
                        "page": page,
                        "pageSize": pageSize,
                        "total": total_cards,
                        "totalPages": (total_cards + pageSize - 1) // pageSize
                    },
                    "source": "regular_recommendations"
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

# 收藏卡片相关API
@router.post("/collect")
async def collect_card(
    card_id: str = Query(..., description="卡片ID"),
    scene_type: str = Query(..., description="场景类型"),
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
        
        # 提交收藏操作
        result = match_service.submit_match_action(
            user_id=user_id,
            action_data={
                "cardId": card_id,
                "action": MatchActionType.COLLECTION.value,
                "sceneType": scene_type,
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
    scene_type: Optional[str] = Query(None, description="场景类型筛选"),
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
            scene_type=scene_type,
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
    
    try:
        # 优先获取AI推荐
        from sqlalchemy import and_
        from app.models.match_action import MatchAction, MatchActionType
        from app.models.user import User
        from app.models.user_card_db import UserCard
        
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 先尝试获取AI推荐
        ai_recommend_actions = db.query(MatchAction).filter(
            and_(
                MatchAction.target_user_id == user_id,
                MatchAction.action_type == MatchActionType.AI_RECOMMEND_AFTER_USER_CHAT
            )
        ).order_by(MatchAction.created_at.desc())
        
        ai_total = ai_recommend_actions.count()
        ai_actions = ai_recommend_actions.offset((page - 1) * pageSize).limit(pageSize).all()
        
        if ai_total > 0:
            # 有AI推荐，返回AI推荐数据
            cards = []
            for action in ai_actions:
                target_user = db.query(User).filter(User.id == str(action.user_id)).first()
                if not target_user:
                    continue
                    
                target_card = db.query(UserCard).filter(
                    UserCard.user_id == str(action.user_id),
                    UserCard.scene_type == sceneType,
                    UserCard.is_active == 1
                ).first()
                
                if not target_card:
                    continue
                
                scene_context = {}
                if action.scene_context:
                    try:
                        scene_context = json.loads(action.scene_context)
                    except:
                        pass
                
                card_data = {
                    "id": str(action.id),
                    "userId": str(target_user.id),
                    "name": getattr(target_user, 'nick_name', None) or getattr(target_user, 'name', '匿名用户'),
                    "avatar": getattr(target_user, 'avatar_url', None),
                    "age": getattr(target_user, 'age', 25),
                    "occupation": getattr(target_user, 'occupation', ''),
                    "location": getattr(target_user, 'location', ''),
                    "bio": getattr(target_user, 'bio', ''),
                    "interests": getattr(target_user, 'interests', []),
                    "sceneType": str(action.action_type),
                    "isAIRecommendation": True,
                    "aiAnalysis": scene_context.get('aiAnalysis', {}),
                    "matchScore": scene_context.get('aiAnalysis', {}).get('matchScore', 85),
                    "recommendationReason": scene_context.get('aiAnalysis', {}).get('preferenceJudgement', '基于聊天内容智能推荐'),
                    "createdAt": action.created_at.isoformat() if action.created_at else ""
                }
                
                if sceneType == "activity":
                    card_data.update({
                        "activityName": getattr(target_card, 'title', ''),
                        "activityTime": getattr(target_card, 'activity_time', ''),
                        "activityLocation": getattr(target_card, 'location', ''),
                        "activityPrice": getattr(target_card, 'price', 0)
                    })
                elif sceneType == "social":
                    card_data.update({
                        "gender": getattr(target_user, 'gender', ''),
                        "education": getattr(target_user, 'education', '')
                    })
                
                cards.append(card_data)
            
            return BaseResponse(
                code=0,
                message="success",
                data={
                    "cards": cards,
                    "pagination": {
                        "page": page,
                        "pageSize": pageSize,
                        "total": ai_total,
                        "totalPages": (ai_total + pageSize - 1) // pageSize
                    },
                    "source": "ai_recommendations"
                }
            )
        else:
            # 没有AI推荐，使用普通匹配推荐
            from app.services.match_service import MatchService
            match_service = MatchService(db)
            
            # 获取匹配卡片
            cards_data = match_service.get_recommendation_cards(
                user_id=user_id,
                scene_type=sceneType,
                user_role=roleType,
                page=page,
                page_size=pageSize
            )
            
            return BaseResponse(
                code=0,
                message="success",
                data={
                    "cards": cards_data.get("cards", []),
                    "pagination": {
                        "page": page,
                        "pageSize": pageSize,
                        "total": cards_data.get("total", 0),
                        "totalPages": (cards_data.get("total", 0) + pageSize - 1) // pageSize
                    },
                    "source": "regular_recommendations"
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