from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database import get_db
from app.services.topic_card_service import TopicCardService
from app.services.vote_service import VoteService
from app.models.user import User
from app.dependencies import get_current_user
from app.services.user_connection_service import UserConnectionService
from app.models.user_card_db import UserCard

router = APIRouter()

@router.get("/cards")
async def get_feed_cards(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    card_type: Optional[str] = Query(None, description="卡片类型: topic, vote, all"),
    category: Optional[str] = Query(None, description="分类筛选"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取统一的卡片流数据
    
    支持获取话题卡片和投票卡片，可以按类型筛选或获取混合内容
    """
    try:
        user_id = str(current_user.get("id")) if current_user else None
        all_cards = []
        
        # 获取话题卡片
        if card_type in ["topic", "all", None]:
            topic_result = TopicCardService.get_topic_cards(
                db=db,
                user_id=user_id,
                page=page,
                page_size=page_size,
                category=category
            )
            
            # 格式化话题卡片数据
            if topic_result and "items" in topic_result:
                for card in topic_result["items"]:
                    formatted_card = {
                        "id": card.id,
                        "type": "topic",
                        "title": card.title,
                        "content": card.description or card.title,
                        "category": card.category,
                        "created_at": card.created_at.isoformat() if hasattr(card, 'created_at') and card.created_at else None,
                        "updated_at": card.updated_at.isoformat() if hasattr(card, 'updated_at') and card.updated_at else None,
                        "user_id": card.user_id,
                        "user_avatar": card.creator_avatar or '',
                        "user_nickname": card.creator_nickname or '匿名用户',
                        "like_count": card.like_count or 0,
                        "comment_count": card.discussion_count or 0,
                        "has_liked": False,  # 默认False，因为TopicCardResponse没有has_liked属性
                        "images": [card.cover_image] if card.cover_image else [],
                        "is_liked": False,  # 默认False，因为TopicCardResponse没有has_liked属性
                        "sceneType": "topic"
                    }
                    all_cards.append(formatted_card)
        
        # 获取投票卡片
        if card_type in ["vote", "all", None]:
            vote_service = VoteService(db)
            recall_votes = vote_service.get_recall_vote_cards(limit=page_size)
            
            # 为每个卡片添加投票状态
            for card in recall_votes:
                vote_results = vote_service.get_vote_results(card.id, user_id)
                # 获取用户信息
                user = db.query(User).filter(User.id == card.user_id).first()
                user_avatar = user.avatar_url if user else ''
                user_nickname = user.nick_name if user else '匿名用户'  # 使用nick_name字段
                
                formatted_card = {
                    "id": card.id,
                    "type": "vote",
                    "vote_type": card.vote_type,
                    "title": card.title,
                    "content": card.description or card.title,
                    "category": card.category,
                    "created_at": card.created_at.isoformat() if hasattr(card, 'created_at') and card.created_at else None,
                    "updated_at": card.updated_at.isoformat() if hasattr(card, 'updated_at') and card.updated_at else None,
                    "user_id": card.user_id,
                    "user_avatar": user_avatar,
                    "user_nickname": user_nickname,
                    "vote_options": vote_results["options"],
                    "total_votes": card.total_votes or 0,
                    "has_voted": vote_results["has_voted"],
                    "user_votes": vote_results["user_votes"],
                    "vote_deadline": card.end_time.isoformat() if hasattr(card, 'end_time') and card.end_time else None,
                    "max_selections": 1,
                    "allow_discussion": True,
                    "images": [card.cover_image] if card.cover_image else [],
                    "sceneType": "vote"
                }
                all_cards.append(formatted_card)
        
        # 按创建时间排序（最新的在前）
        all_cards.sort(key=lambda x: x["created_at"] or "", reverse=True)
        
        # 分页处理
        total = len(all_cards)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = all_cards[start_idx:end_idx]
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "has_next": end_idx < total,
            "has_prev": page > 1
        }
        
    except Exception as e:
        print(f"获取卡片流失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取卡片流失败: {str(e)}")

   
@router.get("/recommendation-user-cards")
async def get_recommendation_user_cards(
    sceneType: Optional[str] = Query(None, description="匹配类型"),
    roleType: Optional[str] = Query(None, description="用户角色"),
    status: Optional[str] = Query(None, description="匹配状态"),
    page: int = Query(1, description="页码"),
    pageSize: int = Query(10, description="每页数量"),
    limit: int = Query(None, description="每页数量(兼容参数)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """    
    推荐逻辑：
    1. 根据用户上次访问(VISIT)时间顺序排列，选取最久未访问的若干用户
    2. 剔除最近两周曾经浏览(VIEW)过的用户
    3. 按顺序展示给用户
    """
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 获取推荐用户列表（根据访问时间排序，排除最近浏览过的）
        print("正在获取推荐用户列表...")
        recommended_users = UserConnectionService.get_recommended_users(
            db=db,
            current_user_id=user_id,
            limit=pageSize * 3  # 获取更多的用户用于筛选有卡片的用户
        )
        
        # 获取推荐用户的ID列表
        recommended_user_ids = [user['id'] for user in recommended_users]
        print(f"推荐用户ID列表: {recommended_user_ids}")
        
        if not recommended_user_ids:
            # 如果没有推荐用户，返回空结果
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "cards": [],
                    "pagination": {
                        "page": page,
                        "pageSize": pageSize,
                        "total": 0,
                        "totalPages": 0
                    },
                    "source": "recommendation_with_visit_logic"
                }
            }
        
        # 查询这些用户的活跃卡片
        print("正在查询推荐用户的卡片...")
        card_query = db.query(UserCard).filter(
            and_(
                UserCard.is_active == 1,
                UserCard.user_id.in_(recommended_user_ids)
            )
        )
        
        # 获取总数
        total_cards = card_query.count()
        print(f"符合条件的卡片总数: {total_cards}")
        
        # 按推荐顺序排序卡片（保持用户的访问时间顺序）
        user_id_order = {user_id: index for index, user_id in enumerate(recommended_user_ids)}
        all_cards = card_query.all()
        
        # 按推荐用户顺序排序卡片
        sorted_cards = sorted(all_cards, key=lambda card: user_id_order.get(card.user_id, float('inf')))
        
        # 分页处理
        offset = (page - 1) * pageSize
        paginated_cards = sorted_cards[offset:offset + pageSize]
        print(f"当前页获取卡片数量: {len(paginated_cards)}")
        
        # 构建返回数据
        cards = []
        print("开始处理卡片数据...")
        
        for i, user_card in enumerate(paginated_cards):
            print(f"处理第{i+1}个卡片: card_id={user_card.id}, user_id={user_card.user_id}")
            
            # 获取卡片创建者信息
            card_creator = db.query(User).filter(User.id == str(user_card.user_id)).first()
            if not card_creator:
                print(f"跳过: 找不到卡片创建者 user_id={user_card.user_id}")
                continue
            
            # 获取用户的推荐信息
            user_recommend_info = next((user for user in recommended_users if user['id'] == user_card.user_id), {})
            
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
                "recommendReason": '最久未访问',
                "cardTitle": str(user_card.display_name),
                "displayName": getattr(user_card, 'display_name', None),
                "visibility": getattr(user_card, 'visibility', 'public'),
                "lastVisitTime": user_recommend_info.get('last_visit_time', None),
                "hasVisited": user_recommend_info.get('connection_info', {}).get('has_visited', False),
                "visitCount": user_recommend_info.get('connection_info', {}).get('visit_count', 0)
            }
            
            cards.append(card_data)
        
        print(f"成功处理卡片数量: {len(cards)}")
        
        return {
            "code": 0,
            "message": "success",
            "data": {
                "cards": cards,
                "pagination": {
                    "page": page,
                    "pageSize": pageSize,
                    "total": total_cards,
                    "totalPages": (total_cards + pageSize - 1) // pageSize
                },
                "source": "recommendation_with_visit_logic"
            }
        }
            
    except Exception as e:
        print(f"获取推荐卡片异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"获取推荐卡片失败: {str(e)}",
            "data": None
        }