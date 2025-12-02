from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.topic_card_service import TopicCardService
from app.services.vote_service import VoteService
from app.models.user import User
from app.dependencies import get_current_user

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
            hot_votes = vote_service.get_hot_vote_cards(limit=page_size)
            
            # 为每个卡片添加投票状态
            for card in hot_votes:
                vote_results = vote_service.get_vote_results(card.id, user_id)
                
                # 获取用户信息
                user = db.query(User).filter(User.id == card.user_id).first()
                user_avatar = user.avatar_url if user else ''
                user_nickname = user.nick_name if user else '匿名用户'  # 使用nick_name字段
                
                formatted_card = {
                    "id": card.id,
                    "type": "vote",
                    "vote_type": "vote",
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
        raise HTTPException(status_code=500, detail=f"获取卡片流失败: {str(e)}")

@router.get("/cards/trending")
async def get_trending_cards(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取热门卡片（综合排序）
    
    基于点赞数、评论数、投票数等综合指标排序
    """
    try:
        user_id = str(current_user.get("id")) if current_user else None
        all_cards = []
        
        # 获取热门话题卡片
        topic_result = TopicCardService.get_topic_cards(
            db=db,
            user_id=user_id,
            page=1,
            page_size=limit
        )
        
        # 获取热门投票卡片
        vote_service = VoteService(db)
        hot_votes = vote_service.get_hot_vote_cards(limit=limit)
        
        # 格式化话题卡片
        if topic_result and "items" in topic_result:
            for card in topic_result["items"]:
                # 计算热门分数（点赞数 + 评论数 * 2）
                hot_score = (card.like_count or 0 + (card.discussion_count or 0) * 2)
                
                formatted_card = {
                    "id": card.id,
                    "type": "topic",
                    "title": card.title,
                    "content": card.description or card.title,
                    "category": card.category,
                    "created_at": card.created_at.isoformat() if hasattr(card, 'created_at') and card.created_at else None,
                    "user_id": card.user_id,
                    "user_avatar": card.creator_avatar or '',
                    "user_nickname": card.creator_nickname or '匿名用户',
                    "like_count": card.like_count or 0,
                    "comment_count": card.discussion_count or 0,
                    "has_liked": False,  # 默认False，因为TopicCardResponse没有has_liked属性
                    "images": [card.cover_image] if card.cover_image else [],
                    "is_liked": False,  # 默认False，因为TopicCardResponse没有has_liked属性
                    "sceneType": "topic",
                    "hot_score": hot_score
                }
                all_cards.append(formatted_card)
        
        # 格式化投票卡片
        for card in hot_votes:
            # 计算热门分数（投票数 + 浏览数 * 0.5）
            hot_score = (card.total_votes or 0 + (card.view_count or 0) * 0.5)
            
            # 获取用户信息
            user = db.query(User).filter(User.id == card.user_id).first()
            user_avatar = user.avatar_url if user else ''
            user_nickname = user.nick_name if user else '匿名用户'  # 使用nick_name字段
            
            # 获取投票结果
            vote_results = vote_service.get_vote_results(card.id, user_id)
            
            formatted_card = {
                "id": card.id,
                "type": "vote",
                "vote_type": "vote",
                "title": card.title,
                "content": card.description or card.title,
                "category": card.category,
                "created_at": card.created_at.isoformat() if hasattr(card, 'created_at') and card.created_at else None,
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
                "sceneType": "vote",
                "hot_score": hot_score
            }
            all_cards.append(formatted_card)
        
        # 按热门分数排序
        all_cards.sort(key=lambda x: x.get("hot_score", 0), reverse=True)
        
        # 限制返回数量
        result_cards = all_cards[:limit]
        
        return {
            "items": result_cards,
            "total": len(result_cards)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热门卡片失败: {str(e)}")