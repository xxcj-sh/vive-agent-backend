from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.sql import func
from sqlalchemy.sql.functions import coalesce
from app.models.user import User
from app.models.user_card_db import UserCard
from app.services.topic_card_service import TopicCardService
from app.services.vote_service import VoteService
from app.services.user_connection_service import UserConnectionService


class FeedService:
    """Feed流服务类，负责处理卡片流相关的业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def _process_media_url(url: str) -> str:
        """
        处理媒体URL，确保返回完整的URL路径
        参考前端 card-formatter.js 的 processMediaUrl 方法
        """
        if not url or url.startswith('http') or url.startswith('wxfile'):
            return url
        
        if url.startswith('/'):
            # 移除 /api/v1 部分，添加服务器基础地址
            base_url = "http://47.117.95.151:8000"  # 可以根据配置动态获取
            return f"{base_url}{url}"
        
        return url
    
    def get_feed_item_cards(self, user_id: Optional[str], page: int, page_size: int, 
                      card_type: Optional[str] = None, category: Optional[str] = None) -> Dict[str, Any]:
        """
        获取统一的卡片流数据
        
        Args:
            user_id: 当前用户ID
            page: 页码
            page_size: 每页数量
            card_type: 卡片类型: topic, vote, all
            category: 分类筛选
            
        Returns:
            包含卡片列表和分页信息的字典
        """
        all_cards = []
        
        # 获取话题卡片
        if card_type in ["topic", "all", None]:
            topic_result = TopicCardService.get_topic_cards(
                db=self.db,
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
                        "sceneType": "topic",
                        "is_anonymous": card.is_anonymous or 0
                    }
                    all_cards.append(formatted_card)
        
        # 获取投票卡片
        if card_type in ["vote", "all", None]:
            vote_service = VoteService(self.db)
            recall_votes = vote_service.get_recall_vote_cards(limit=page_size, user_id=user_id)
            # 为每个卡片添加投票状态
            for card in recall_votes:
                vote_results = vote_service.get_vote_results(card.id, user_id)
                # 获取用户信息（只获取活跃用户）
                user = self.db.query(User).filter(
                    User.id == card.user_id,
                    User.is_active == True
                ).first()
                user_avatar = user.avatar_url if user else ''
                user_nickname = user.nick_name if user else '匿名用户'  # 使用nick_name字段
                
                # 如果用户不存在或已注销，跳过此卡片
                if not user:
                    continue
                
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
        
        # 按创建时间排序（最旧的在前），确保 category='basic' 置顶，再按创建时间倒序
        all_cards.sort(key=lambda x: (x.get("category") != "basic", x["created_at"] or ""), reverse=False)
        
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
    
    def get_random_public_user_cards(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取随机的公开用户卡片（用于未登录用户）
        
        Args:
            limit: 返回卡片数量限制
        
        Returns:
            格式化的用户卡片列表
        """
        try:
            # 查询公开且活跃的用户卡片
            public_cards = self.db.query(UserCard).filter(
                and_(
                    UserCard.visibility == "public",
                    UserCard.is_active == 1,
                    coalesce(UserCard.is_deleted, 0) != 1
                )
            ).order_by(func.random()).limit(limit).all()
            if not public_cards:
                return []
            
            # 格式化卡片数据
            formatted_cards = []
            for card in public_cards:  
                user = self.db.query(User).filter(
                    and_(
                        User.id == card.user_id,
                        User.is_active == 1
                    )
                ).first()
                # 如果用户不存在或已注销，跳过此卡片
                if not user:
                    continue
                
                card_data = {
                    # 基础信息
                    "id": str(card.id),
                    "userId": str(card.user_id),
                    "name": getattr(card, 'display_name', None),
                    "avatar": self._process_media_url(getattr(card, 'avatar_url', None) or getattr(user, 'avatar_url', None) or ""),
                    "age": getattr(user, 'age', 25),
                    "occupation": getattr(user, 'occupation', ''),
                    "location": getattr(card, 'location', ''),
                    "bio": getattr(card, 'bio', '') or '这个人很懒，什么都没有留下...',
                    "interests": getattr(user, 'interests', []) if isinstance(getattr(user, 'interests', []), list) else [],
                    
                    # 场景和角色信息
                    "cardType": 'social',
                    "isTopicCard": False,
                    "card_size": 'large',
                    
                    # 推荐相关字段（未登录用户默认状态）
                    "isRecommendation": False,
                    "recommendationReason": '随机推荐',
                    "matchScore": 0,
                    "hasInterestInMe": False,
                    "mutualMatchAvailable": False,
                    
                    # 访问记录（未登录用户默认状态）
                    "lastVisitTime": None,
                    "hasVisited": False,
                    "visitCount": 0,
                    
                    # 其他字段
                    "createdAt": card.created_at.isoformat() if card.created_at else "",
                    "displayName": getattr(card, 'display_name', None),
                    "creatorName": getattr(user, 'nick_name', '匿名用户'),
                    "creatorAvatar": self._process_media_url(getattr(user, 'avatar_url', None) or ""),
                    "creatorAge": getattr(user, 'age', 25),
                    "creatorOccupation": getattr(user, 'occupation', ''),
                    "cardTitle": str(card.display_name),
                    "visibility": 'everyone' if getattr(card, 'visibility', 'public') == 'public' else getattr(card, 'visibility', 'public')
                }                
                formatted_cards.append(card_data)
            
            return formatted_cards
            
        except Exception as e:
            print(f"获取随机公开用户卡片失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_feed_user_cards(self, user_id: str, page: int, page_size: int) -> Dict[str, Any]:
        """
        获取推荐用户卡片
        
        推荐逻辑：
        1. 根据用户上次访问(VISIT)时间顺序排列，选取最久未访问的若干用户
        2. 剔除最近两周曾经浏览(VIEW)过的用户
        3. 按顺序展示给用户
        
        Args:
            user_id: 当前用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            包含推荐卡片和分页信息的字典
        """
        try:
            # 获取推荐用户列表（根据访问时间排序，排除最近浏览过的）
            recommended_users = UserConnectionService.get_recommended_users(
                db=self.db,
                current_user_id=user_id,
                limit=page_size * 3  # 获取更多的用户用于筛选有卡片的用户
            )
            
            # 获取推荐用户的ID列表
            recommended_user_ids = [user['id'] for user in recommended_users]
            
            if not recommended_user_ids:
                # 如果没有推荐用户，返回空结果
                return {
                    "cards": [],
                    "pagination": {
                        "page": page,
                        "pageSize": page_size,
                        "total": 0,
                        "totalPages": 0
                    },
                    "source": "recommendation_with_visit_logic"
                }
            
            # 查询这些用户的活跃卡片
            card_query = self.db.query(UserCard).filter(
                and_(
                    UserCard.is_active == 1,
                    UserCard.is_deleted == 0,
                    UserCard.user_id.in_(recommended_user_ids)
                )
            )
            
            # 获取总数
            total_cards = card_query.count()
            
            # 按推荐顺序排序卡片（保持用户的访问时间顺序）
            user_id_order = {user_id: index for index, user_id in enumerate(recommended_user_ids)}
            all_cards = card_query.all()
            
            # 按推荐用户顺序排序卡片
            sorted_cards = sorted(all_cards, key=lambda card: user_id_order.get(card.user_id, float('inf')))
            
            # 分页处理
            offset = (page - 1) * page_size
            paginated_cards = sorted_cards[offset:offset + page_size]
            
            # 构建返回数据
            cards = []
            
            for i, user_card in enumerate(paginated_cards):                
                # 获取卡片创建者信息，并检查用户状态
                card_creator = self.db.query(User).filter(
                    and_(
                        User.id == str(user_card.user_id),
                        User.is_active == 1
                    )
                ).first()
                if not card_creator:
                    print(f"跳过: 找不到卡片创建者或用户已注销 user_id={user_card.user_id}")
                    continue
                
                # 获取用户的推荐信息
                user_recommend_info = next((user for user in recommended_users if user['id'] == user_card.user_id), {})
                # 构建前端兼容的格式化卡片数据
                card_data = {
                    # 基础信息
                    "id": str(user_card.id),
                    "userId": str(card_creator.id),
                    "avatar": self._process_media_url(getattr(user_card, 'avatar_url', None) or getattr(card_creator, 'avatar_url', None) or ""),
                    "age": getattr(card_creator, 'age', 25),
                    "occupation": getattr(card_creator, 'occupation', ''),
                    "location": getattr(user_card, 'location', ''),
                    "bio": getattr(user_card, 'bio', '') or '这个人很懒，什么都没有留下...',
                    "interests": getattr(card_creator, 'interests', []) if isinstance(getattr(card_creator, 'interests', []), list) else [],
                    
                    # 场景和角色信息
                    "cardType": 'social',
                    "isTopicCard": False,
                    "card_size": 'large',
                    
                    # 推荐相关字段
                    "isRecommendation": True,
                    "recommendationReason": '最久未访问',
                    "matchScore": 0,
                    "hasInterestInMe": False,
                    "mutualMatchAvailable": False,
                    
                    # 访问记录
                    "lastVisitTime": user_recommend_info.get('last_visit_time', None) if user_recommend_info else None,
                    "hasVisited": user_recommend_info.get('connection_info', {}).get('has_visited', False) if user_recommend_info and user_recommend_info.get('connection_info') else False,
                    "visitCount": user_recommend_info.get('connection_info', {}).get('visit_count', 0) if user_recommend_info and user_recommend_info.get('connection_info') else 0,
                    
                    # 其他字段（兼容前端格式）
                    "createdAt": user_card.created_at.isoformat() if user_card.created_at else "",
                    "displayName": getattr(user_card, 'display_name', None),
                    "creatorName": getattr(card_creator, 'nick_name', '匿名用户'),
                    "creatorAvatar": self._process_media_url(getattr(card_creator, 'avatar_url', None) or ""),
                    "creatorAge": getattr(card_creator, 'age', 25),
                    "creatorOccupation": getattr(card_creator, 'occupation', ''),
                    "cardTitle": str(user_card.display_name),
                    "visibility": 'everyone' if getattr(user_card, 'visibility', 'public') == 'public' else getattr(user_card, 'visibility', 'public')
                }
                
                cards.append(card_data)
            
            print(f"成功处理卡片数量: {len(cards)}")
            
            return {
                "cards": cards,
                "pagination": {
                    "page": page,
                    "pageSize": page_size,
                    "total": total_cards,
                    "totalPages": (total_cards + page_size - 1) // page_size
                },
                "source": "recommendation_with_visit_logic"
            }
                
        except Exception as e:
            print(f"获取推荐卡片异常: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e