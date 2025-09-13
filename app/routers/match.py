import json
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
    sceneType: str = Query(...),
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
            match_type=sceneType,
            user_role=userRole,
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
            match_type=sceneType,
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

@router.get("/recommendations")
async def get_match_recommendations(
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
    
    统一使用 /api/v1/matches/recommendations 端点
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
        
        # 先尝试获取AI推荐
        ai_recommend_actions = db.query(MatchAction).filter(
            and_(
                MatchAction.target_user_id == user_id,
                MatchAction.action_type == MatchActionType.AI_RECOMMEND_AFTER_USER_CHAT
            )
        ).order_by(MatchAction.created_at.desc())
        ai_total = ai_recommend_actions.count()
        ai_actions = ai_recommend_actions.offset((page - 1) * pageSize).limit(pageSize).all()
        print("ai_actions", ai_actions)
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
                    "sceneType": str(action.match_type),
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

@router.get("/{match_id}")
async def get_match_detail(
    match_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取匹配推荐列表
    
    统一使用 /api/v1/matches/recommendations 端点
    """
    print("=== Match Recommendations API Called ===")
    print(f"URL: /api/v1/matches/recommendations")
    print(f"Parameters: sceneType={sceneType}, roleType={roleType}, status={status}, page={page}, pageSize={pageSize}, limit={limit}")
    
    # 处理兼容参数
    if limit is not None and pageSize == 10:  # 如果提供了limit且pageSize是默认值
        pageSize = limit
    
    # 如果提供了status参数，使用获取用户匹配列表的逻辑
    if status is not None:
        try:
            from app.services.match_service import MatchService
            match_service = MatchService(db)
            
            # 获取当前用户ID
            if isinstance(current_user, dict):
                user_id = str(current_user.get('id', ''))
            else:
                user_id = str(current_user.id)
            
            # 获取用户匹配列表
            matches_data = match_service.get_user_matches(
                user_id=user_id,
                status=status,
                page=page,
                page_size=pageSize
            )
            
            return BaseResponse(
                code=0,
                message="success",
                data={
                    "matches": matches_data.get("matches", []),
                    "pagination": {
                        "page": page,
                        "pageSize": pageSize,
                        "total": matches_data.get("total", 0),
                        "totalPages": (matches_data.get("total", 0) + pageSize - 1) // pageSize
                    }
                }
            )
            
        except Exception as e:
            print(f"获取用户匹配列表异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return BaseResponse(
                code=500,
                message=f"获取用户匹配列表失败: {str(e)}",
                data=None
            )
    
    # 检查必需参数
    if sceneType is None or roleType is None:
        return BaseResponse(
            code=422,
            message="参数错误：sceneType和roleType是必需的参数",
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
                    "sceneType": str(action.match_type),
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