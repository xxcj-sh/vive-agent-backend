import random
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.dependencies import get_current_user
from app.services.feed_service import FeedService
from app.services.recommendation_service import RecommendationService
from app.services.topic_recommendation_service import TopicRecommendationService

router = APIRouter()

@router.get("/unified")
async def get_unified_feed_cards(
    limit: int = Query(default=20, ge=1, le=50, description="返回卡片数量限制"),
    gender: Optional[str] = Query(default=None, description="性别筛选"),
    city: Optional[str] = Query(default=None, description="城市筛选"),
    min_age: Optional[int] = Query(default=None, ge=0, le=150, description="最小年龄"),
    max_age: Optional[int] = Query(default=None, ge=0, le=150, description="最大年龄"),
    include_topics: bool = Query(default=True, description="是否包含话题/投票卡片推荐"),
    tag_id: Optional[str] = Query(default=None, description="社群标签ID，用于筛选特定社群的内容"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取统一的推荐卡片流（用户推荐 + 话题/投票卡片推荐）

    推荐流程：
    1. 召回阶段：根据多种策略召回候选用户（社群标签、社交关系、用户标签等）
       以及话题/投票卡片（基于社群标签、社交兴趣等）
    2. 过滤阶段：应用用户设置的过滤条件（性别、城市、年龄）
    3. 排序阶段：根据用户偏好和相关性排序
    4. 整合输出：将话题推荐结果插入到用户推荐结果中

    召回策略：
    - 社群用户召回：召回拥有共同社群标签的用户
    - 社交关系召回：召回长期未联络的朋友
    - 用户标签召回：基于用户画像标签召回相似用户
    - 活跃用户召回：补充活跃用户
    - 社群话题/投票召回：召回社群群主发布的话题和投票卡片
    - 社交兴趣话题/投票召回：召回用户感兴趣的人发布的内容

    社群筛选模式（当传入 tag_id 时）：
    - 只返回该社群成员的用户卡片
    - 只返回该社群成员发布的话题和投票卡片
    - 其他召回策略将被禁用，避免干扰社群筛选结果

    排序因子：
    - 标签匹配度（共同标签数量）
    - 活跃度（最近更新时间）
    - 资料完整度

    Args:
        limit: 返回卡片数量限制（1-50，默认20）
        gender: 性别筛选（male/female/other）
        city: 城市筛选
        min_age: 最小年龄
        max_age: 最大年龄
        include_topics: 是否包含话题/投票卡片推荐（默认True）
        tag_id: 社群标签ID，用于筛选特定社群的内容
        current_user: 当前用户信息（可选，未登录时使用冷启动策略）
        db: 数据库会话

    Returns:
        推荐卡片列表（包含用户卡片和话题/投票卡片）
    """
    try:
        feed_service = FeedService(db)
        
        # 如果指定了社群标签筛选，使用独立的社群筛选策略
        if tag_id:
            print(f"[FeedRouter] 社群筛选模式 - tag_id: {tag_id}")
            user_id = current_user["id"] if current_user else None
            
            # 调用支持社群筛选的 feed 服务方法
            community_result = feed_service.get_unified_feed_cards(
                user_id=user_id,
                page=1,
                page_size=limit,
                tag_id=tag_id
            )
            
            # 转换返回格式
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "items": community_result.get("items", []),
                    "total": community_result.get("total", 0),
                    "has_more": community_result.get("has_next", False)
                }
            }
        
        # 未登录用户使用冷启动策略
        if not current_user:
            print(f"[FeedRouter] 未登录用户请求统一推荐卡片")
            cold_start_user_cards = feed_service.get_cold_start_user_cards(limit)
            
            # 收集用户卡片
            user_items = []
            for user in cold_start_user_cards["data"].get("users", []):
                user_items.append({
                    "id": user.get("id"),
                    "user_id": user.get("user_id"),
                    "avatar": user.get("avatar_url"),
                    "user_avatar": user.get("avatar_url"),
                    "display_name": user.get("display_name"),
                    "bio": user.get("bio"),
                    "role_type": user.get("role_type"),
                    "card_type": "user",
                    "tags": [],
                    "created_at": None,
                    "view_count": 0,
                    "discussion_count": 0
                })
            
            # 收集话题/投票卡片（优先展示投票卡片）
            topic_items = []
            vote_items = []
            if include_topics:
                cold_start_topic_cards = feed_service.get_cold_start_topic_cards(limit=limit)
                topic_items = cold_start_topic_cards["data"].get("topic_cards", [])
                vote_items = cold_start_topic_cards["data"].get("vote_cards", [])
            
            random.seed()  # 使用当前时间作为随机种子
            
            items = []
            
            # 先添加投票卡片（如果有）
            if vote_items:
                items.append(vote_items[0])
                # 将用户卡片、话题卡片和剩余投票卡片合并后混洗
                cards_to_shuffle = user_items + topic_items + vote_items[1:]
            else:
                # 没有投票卡片时，直接混洗用户卡片和话题卡片
                cards_to_shuffle = user_items + topic_items
            
            random.shuffle(cards_to_shuffle)
            items.extend(cards_to_shuffle)
            
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "items": items,
                    "total": len(items),
                    "has_more": False
                }
            }


        # 构建过滤条件
        filters = {}
        if gender:
            filters['gender'] = gender
        if city:
            filters['city'] = city
        if min_age is not None and max_age is not None:
            filters['age_range'] = [min_age, max_age]


        # 已登录用户获取个性化推荐（非社群筛选模式）
        user_id = current_user["id"]
        
        # 获取用户推荐
        result = feed_service.get_recommended_user_cards(
            current_user_id=user_id,
            limit=limit,
            filters=filters if filters else None
        )

        # 转换用户卡片数据格式
        user_items = []
        for card in result["data"].get("users", []):
            user_items.append({
                "id": card.get("id"),
                "user_id": card.get("user_id"),
                "avatar": card.get("avatar_url"),
                "user_avatar": card.get("avatar_url"),
                "display_name": card.get("display_name"),
                "bio": card.get("bio"),
                "role_type": card.get("role_type"),
                "recommend_score": card.get("recommend_score"),
                "created_at": card.get("updated_at"),
                "view_count": 0,
                "discussion_count": 0,
                "card_type": "user",
                "tags": []
            })
        # 收集话题/投票卡片
        topic_items = []
        vote_items = []
        # 获取话题/投票卡片推荐
        if include_topics:
            topic_cards_result = feed_service.get_recommended_topic_cards(
                user_id=user_id,
                topic_limit=8,
                vote_limit=5
            )
            topic_items = topic_cards_result["data"].get("topic_cards", [])
            vote_items = topic_cards_result["data"].get("vote_cards", [])
       
        # 将用户卡片和话题卡片合并后混洗
        cards_to_shuffle = user_items + vote_items + topic_items
        random.shuffle(cards_to_shuffle)
        # 限制返回数量
        items = cards_to_shuffle[:limit]
        print(f"[FeedRouter] 推荐卡片总数: {len(items)}")

        return {
            "code": result["code"],
            "message": result["message"],
            "data": {
                "items": items,
                "total": len(items),
                "has_more": result["data"].get("has_more", False)
            }
        }

    except Exception as e:
        print(f"[FeedRouter] 获取统一推荐卡片失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"获取推荐卡片失败: {str(e)}",
            "data": {
                "items": [],
                "total": 0,
                "has_more": False
            }
        }


@router.get("/debug/recall")
async def debug_recall_strategies(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    调试接口：查看各召回策略的结果
    
    用于测试和调试推荐系统的召回策略
    
    Args:
        request: 请求对象
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        各召回策略的结果统计
    """
    try:
        service = RecommendationService(db)
        topic_service = TopicRecommendationService(db)
        user_id = current_user["id"]
        
        # 获取排除列表
        excluded_ids = service.get_excluded_user_ids(user_id)
        excluded_topic_ids = topic_service.get_excluded_topic_card_ids(user_id)
        excluded_vote_ids = topic_service.get_excluded_vote_card_ids(user_id)
        
        # 测试用户召回策略
        community_users = service.recall_by_community_tags(user_id, excluded_ids)
        social_users = service.recall_by_social_relations(user_id, excluded_ids)
        tag_users = service.recall_by_user_tags(user_id, excluded_ids)
        active_users = service.recall_active_users(user_id, excluded_ids)
        
        # 测试话题/投票卡片召回策略
        community_topics = topic_service.recall_topic_cards_by_community_tags(user_id, excluded_topic_ids)
        social_topics = topic_service.recall_topic_cards_by_social_interest(user_id, excluded_topic_ids)
        active_topics = topic_service.recall_active_topic_cards(user_id, excluded_topic_ids)
        
        community_votes = topic_service.recall_vote_cards_by_community_tags(user_id, excluded_vote_ids)
        social_votes = topic_service.recall_vote_cards_by_social_interest(user_id, excluded_vote_ids)
        active_votes = topic_service.recall_active_vote_cards(user_id, excluded_vote_ids)
        
        return {
            "code": 0,
            "message": "success",
            "data": {
                "excluded_counts": {
                    "users": len(excluded_ids),
                    "topic_cards": len(excluded_topic_ids),
                    "vote_cards": len(excluded_vote_ids)
                },
                "user_recall_strategies": {
                    "community_tags": {
                        "count": len(community_users),
                        "users": [{"id": u.id, "name": u.nick_name} for u in community_users[:5]]
                    },
                    "social_relations": {
                        "count": len(social_users),
                        "users": [{"id": u.id, "name": u.nick_name} for u in social_users[:5]]
                    },
                    "user_tags": {
                        "count": len(tag_users),
                        "users": [{"id": u.id, "name": u.nick_name} for u in tag_users[:5]]
                    },
                    "active_users": {
                        "count": len(active_users),
                        "users": [{"id": u.id, "name": u.nick_name} for u in active_users[:5]]
                    }
                },
                "topic_card_recall_strategies": {
                    "community_tags": {
                        "count": len(community_topics),
                        "cards": [{"id": t.id, "title": t.title} for t in community_topics[:5]]
                    },
                    "social_interest": {
                        "count": len(social_topics),
                        "cards": [{"id": t.id, "title": t.title} for t in social_topics[:5]]
                    },
                    "active": {
                        "count": len(active_topics),
                        "cards": [{"id": t.id, "title": t.title} for t in active_topics[:5]]
                    }
                },
                "vote_card_recall_strategies": {
                    "community_tags": {
                        "count": len(community_votes),
                        "cards": [{"id": v.id, "title": v.title} for v in community_votes[:5]]
                    },
                    "social_interest": {
                        "count": len(social_votes),
                        "cards": [{"id": v.id, "title": v.title} for v in social_votes[:5]]
                    },
                    "active": {
                        "count": len(active_votes),
                        "cards": [{"id": v.id, "title": v.title} for v in active_votes[:5]]
                    }
                },
                "total_recalled": {
                    "users": len(community_users) + len(social_users) + len(tag_users) + len(active_users),
                    "topic_cards": len(community_topics) + len(social_topics) + len(active_topics),
                    "vote_cards": len(community_votes) + len(social_votes) + len(active_votes)
                }
            }
        }
        
    except Exception as e:
        print(f"[FeedRouter] 调试召回策略失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"调试失败: {str(e)}",
            "data": {}
        }