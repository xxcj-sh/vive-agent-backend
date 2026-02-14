"""
话题/投票卡片推荐服务 - 策略层
提供话题和投票卡片的召回策略、排序算法、过滤逻辑等支持服务

设计参考: vive-agent-dev-reference/产品设计/推荐设计/推荐系统第 2 版.md
"""

from typing import Optional, List, Dict, Any, Set, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
import random

from app.models.topic_card_db import TopicCard
from app.models.vote_card_db import VoteCard, VoteRecord
from app.models.tag import Tag, UserTagRel, TagType, UserTagRelStatus
from app.models.user import User
from app.models.user_connection import UserConnection, ConnectionType


class TopicRecommendationService:
    """
    话题/投票卡片推荐系统策略服务类
    
    职责：
    1. 提供话题/投票卡片的各种召回策略的实现
    2. 提供排序算法实现
    3. 提供卡片过滤和排除逻辑
    
    被 FeedService 调用，不直接对外暴露
    """
    
    # 推荐配置参数
    RECALL_LIMIT = 100  # 召回阶段最大数量
    RANK_LIMIT = 50     # 排序阶段输出数量
    RECENT_VIEW_DAYS = 14  # 最近浏览天数
    COLD_START_USER_ID = "xiaojingling-001"  # 冷启动专用投票卡片用户ID
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 召回策略 ====================
    
    def recall_topic_cards_by_community_tags(
        self,
        current_user_id: str,
        excluded_card_ids: Set[str],
        limit: int = 30
    ) -> List[TopicCard]:
        """
        策略1: 基于社群标签的话题卡片召回
        
        召回社群群主发布的话题卡片，帮助创作者在社群中分享话题
        
        Args:
            current_user_id: 当前用户ID
            excluded_card_ids: 需要排除的卡片ID集合
            limit: 召回数量限制
            
        Returns:
            召回的话题卡片列表
        """
        try:
            # 获取当前用户的社群标签
            user_community_tags = self.db.query(UserTagRel.tag_id).filter(
                and_(
                    UserTagRel.user_id == current_user_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE
                )
            ).join(Tag, UserTagRel.tag_id == Tag.id).filter(
                Tag.tag_type == TagType.USER_COMMUNITY
            ).all()
            
            if not user_community_tags:
                return []
            
            tag_ids = [tag_id[0] for tag_id in user_community_tags]
            
            # 获取社群标签的创建者（群主）
            tag_creators = self.db.query(Tag.create_user_id).filter(
                Tag.id.in_(tag_ids)
            ).distinct().all()
            
            creator_ids = [c[0] for c in tag_creators]
            
            # 召回群主发布的话题卡片
            query = self.db.query(TopicCard).filter(
                and_(
                    TopicCard.user_id.in_(creator_ids),
                    TopicCard.is_active == 1,
                    TopicCard.is_deleted == 0,
                    TopicCard.visibility == "public"
                )
            ).order_by(desc(TopicCard.created_at))
            
            if excluded_card_ids:
                query = query.filter(~TopicCard.id.in_(excluded_card_ids))
            
            return query.limit(limit).all()
            
        except Exception as e:
            print(f"[TopicRecommendationService] 社群标签话题召回失败: {str(e)}")
            return []
    
    def recall_vote_cards_by_community_tags(
        self,
        current_user_id: str,
        excluded_card_ids: Set[str],
        limit: int = 30
    ) -> List[VoteCard]:
        """
        策略1: 基于社群标签的投票卡片召回
        
        召回社群群主发布的投票卡片，帮助创作者在社群中调研用户
        
        Args:
            current_user_id: 当前用户ID
            excluded_card_ids: 需要排除的卡片ID集合
            limit: 召回数量限制
            
        Returns:
            召回的投票卡片列表
        """
        try:
            # 获取当前用户的社群标签
            user_community_tags = self.db.query(UserTagRel.tag_id).filter(
                and_(
                    UserTagRel.user_id == current_user_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE
                )
            ).join(Tag, UserTagRel.tag_id == Tag.id).filter(
                Tag.tag_type == TagType.USER_COMMUNITY
            ).all()
            
            if not user_community_tags:
                return []
            
            tag_ids = [tag_id[0] for tag_id in user_community_tags]
            
            # 获取社群标签的创建者（群主）
            tag_creators = self.db.query(Tag.create_user_id).filter(
                Tag.id.in_(tag_ids)
            ).distinct().all()
            
            creator_ids = [c[0] for c in tag_creators]
            
            # 召回群主发布的投票卡片
            query = self.db.query(VoteCard).filter(
                and_(
                    VoteCard.user_id.in_(creator_ids),
                    VoteCard.is_active == 1,
                    VoteCard.is_deleted == 0,
                    VoteCard.visibility == "public"
                )
            ).order_by(desc(VoteCard.created_at))
            
            if excluded_card_ids:
                query = query.filter(~VoteCard.id.in_(excluded_card_ids))
            
            return query.limit(limit).all()
            
        except Exception as e:
            print(f"[TopicRecommendationService] 社群标签投票召回失败: {str(e)}")
            return []
    
    def recall_topic_cards_by_social_interest(
        self,
        current_user_id: str,
        excluded_card_ids: Set[str],
        limit: int = 30
    ) -> List[TopicCard]:
        """
        策略2: 基于社交兴趣的话题卡片召回
        
        召回用户感兴趣的人发布的话题卡片
        
        Args:
            current_user_id: 当前用户ID
            excluded_card_ids: 需要排除的卡片ID集合
            limit: 召回数量限制
            
        Returns:
            召回的话题卡片列表
        """
        try:
            # 获取用户感兴趣的人（基于访问历史和互动）
            interested_user_ids = self._get_interested_user_ids(current_user_id)
            
            if not interested_user_ids:
                return []
            
            # 召回这些人发布的话题卡片
            query = self.db.query(TopicCard).filter(
                and_(
                    TopicCard.user_id.in_(interested_user_ids),
                    TopicCard.is_active == 1,
                    TopicCard.is_deleted == 0,
                    TopicCard.visibility == "public"
                )
            ).order_by(desc(TopicCard.created_at))
            
            if excluded_card_ids:
                query = query.filter(~TopicCard.id.in_(excluded_card_ids))
            
            return query.limit(limit).all()
            
        except Exception as e:
            print(f"[TopicRecommendationService] 社交兴趣话题召回失败: {str(e)}")
            return []
    
    def recall_vote_cards_by_social_interest(
        self,
        current_user_id: str,
        excluded_card_ids: Set[str],
        limit: int = 30
    ) -> List[VoteCard]:
        """
        策略2: 基于社交兴趣的投票卡片召回
        
        召回用户感兴趣的人发布的投票卡片
        
        Args:
            current_user_id: 当前用户ID
            excluded_card_ids: 需要排除的卡片ID集合
            limit: 召回数量限制
            
        Returns:
            召回的投票卡片列表
        """
        try:
            # 获取用户感兴趣的人（基于访问历史和互动）
            interested_user_ids = self._get_interested_user_ids(current_user_id)
            
            if not interested_user_ids:
                return []
            
            # 召回这些人发布的投票卡片
            query = self.db.query(VoteCard).filter(
                and_(
                    VoteCard.user_id.in_(interested_user_ids),
                    VoteCard.is_active == 1,
                    VoteCard.is_deleted == 0,
                    VoteCard.visibility == "public"
                )
            ).order_by(desc(VoteCard.created_at))
            
            if excluded_card_ids:
                query = query.filter(~VoteCard.id.in_(excluded_card_ids))
            
            return query.limit(limit).all()
            
        except Exception as e:
            print(f"[TopicRecommendationService] 社交兴趣投票召回失败: {str(e)}")
            return []
    
    def recall_cold_start_topic_cards(
        self,
        excluded_card_ids: Set[str],
        limit: int = 20
    ) -> List[TopicCard]:
        """
        策略3: 冷启动兜底话题卡片召回
        
        对于未登录或冷启动阶段的新用户，召回热门话题卡片
        
        Args:
            excluded_card_ids: 需要排除的卡片ID集合
            limit: 召回数量限制
            
        Returns:
            召回的话题卡片列表
        """
        try:
            query = self.db.query(TopicCard).filter(
                and_(
                    TopicCard.is_active == 1,
                    TopicCard.is_deleted == 0,
                    TopicCard.visibility == "public"
                )
            )
            
            if excluded_card_ids:
                query = query.filter(~TopicCard.id.in_(excluded_card_ids))
            
            # 按热度和时间排序
            return query.order_by(
                desc(TopicCard.discussion_count + TopicCard.like_count),
                desc(TopicCard.created_at)
            ).limit(limit).all()
            
        except Exception as e:
            print(f"[TopicRecommendationService] 冷启动话题召回失败: {str(e)}")
            return []
    
    def recall_cold_start_vote_cards(
        self,
        excluded_card_ids: Set[str],
        limit: int = 20
    ) -> List[VoteCard]:
        """
        策略3: 冷启动兜底投票卡片召回
        
        召回冷启动专用投票卡片（xiaojingling-001 用户创建）
        以及热门投票卡片
        
        Args:
            excluded_card_ids: 需要排除的卡片ID集合
            limit: 召回数量限制
            
        Returns:
            召回的投票卡片列表
        """
        try:
            # 优先召回冷启动专用投票卡片
            cold_start_cards = self.db.query(VoteCard).filter(
                and_(
                    VoteCard.user_id == self.COLD_START_USER_ID,
                    VoteCard.is_active == 1,
                    VoteCard.is_deleted == 0,
                    VoteCard.visibility == "public"
                )
            ).order_by(desc(VoteCard.created_at)).limit(limit).all()
            
            # 如果冷启动卡片不足，补充热门投票卡片
            if len(cold_start_cards) < limit:
                remaining_limit = limit - len(cold_start_cards)
                
                query = self.db.query(VoteCard).filter(
                    and_(
                        VoteCard.is_active == 1,
                        VoteCard.is_deleted == 0,
                        VoteCard.visibility == "public"
                    )
                )
                
                if excluded_card_ids:
                    query = query.filter(~VoteCard.id.in_(excluded_card_ids))
                
                # 排除已召回的冷启动卡片
                cold_start_ids = {c.id for c in cold_start_cards}
                if cold_start_ids:
                    query = query.filter(~VoteCard.id.in_(cold_start_ids))
                
                hot_cards = query.order_by(
                    desc(VoteCard.total_votes),
                    desc(VoteCard.view_count),
                    desc(VoteCard.created_at)
                ).limit(remaining_limit).all()
                
                return cold_start_cards + hot_cards
            
            return cold_start_cards
            
        except Exception as e:
            print(f"[TopicRecommendationService] 冷启动投票召回失败: {str(e)}")
            return []
    
    def recall_active_topic_cards(
        self,
        current_user_id: Optional[str],
        excluded_card_ids: Set[str],
        limit: int = 30
    ) -> List[TopicCard]:
        """
        策略4: 补充召回 - 活跃话题卡片
        
        当其他召回策略不足时，补充活跃的话题卡片
        
        Args:
            current_user_id: 当前用户ID（可选）
            excluded_card_ids: 需要排除的卡片ID集合
            limit: 召回数量限制
            
        Returns:
            召回的话题卡片列表
        """
        try:
            query = self.db.query(TopicCard).filter(
                and_(
                    TopicCard.is_active == 1,
                    TopicCard.is_deleted == 0,
                    TopicCard.visibility == "public"
                )
            )
            
            if excluded_card_ids:
                query = query.filter(~TopicCard.id.in_(excluded_card_ids))
            
            # 排除当前用户自己创建的
            if current_user_id:
                query = query.filter(TopicCard.user_id != current_user_id)
            
            return query.order_by(desc(TopicCard.updated_at)).limit(limit).all()
            
        except Exception as e:
            print(f"[TopicRecommendationService] 活跃话题召回失败: {str(e)}")
            return []
    
    def recall_active_vote_cards(
        self,
        current_user_id: Optional[str],
        excluded_card_ids: Set[str],
        limit: int = 30
    ) -> List[VoteCard]:
        """
        策略4: 补充召回 - 活跃投票卡片
        
        当其他召回策略不足时，补充活跃的投票卡片
        
        Args:
            current_user_id: 当前用户ID（可选）
            excluded_card_ids: 需要排除的卡片ID集合
            limit: 召回数量限制
            
        Returns:
            召回的投票卡片列表
        """
        try:
            query = self.db.query(VoteCard).filter(
                and_(
                    VoteCard.is_active == 1,
                    VoteCard.is_deleted == 0,
                    VoteCard.visibility == "public"
                )
            )
            
            if excluded_card_ids:
                query = query.filter(~VoteCard.id.in_(excluded_card_ids))
            
            # 排除当前用户自己创建的
            if current_user_id:
                query = query.filter(VoteCard.user_id != current_user_id)
            
            return query.order_by(desc(VoteCard.updated_at)).limit(limit).all()
            
        except Exception as e:
            print(f"[TopicRecommendationService] 活跃投票召回失败: {str(e)}")
            return []
    
    # ==================== 排序策略 ====================
    
    def rank_topic_cards(
        self,
        current_user_id: str,
        topic_cards: List[TopicCard],
        limit: int
    ) -> List[Tuple[TopicCard, float]]:
        """
        排序阶段：根据用户偏好对话题卡片排序
        
        排序因子：
        1. 创作者匹配度（是否为用户感兴趣的人）
        2. 互动热度（讨论数、点赞数）
        3. 新鲜度（创建时间）
        4. 随机因子（增加多样性）
        
        Args:
            current_user_id: 当前用户ID
            topic_cards: 召回的话题卡片列表
            limit: 返回数量限制
            
        Returns:
            [(topic_card, score), ...] 按分数降序排列
        """
        if not topic_cards:
            return []
        
        # 获取用户感兴趣的人
        interested_user_ids = self._get_interested_user_ids(current_user_id)
        
        scored_cards = []
        for card in topic_cards:
            score = self._calculate_topic_card_score(card, interested_user_ids)
            scored_cards.append((card, score))
        
        # 按分数降序排序
        scored_cards.sort(key=lambda x: x[1], reverse=True)
        
        return scored_cards[:limit]
    
    def rank_vote_cards(
        self,
        current_user_id: str,
        vote_cards: List[VoteCard],
        limit: int
    ) -> List[Tuple[VoteCard, float]]:
        """
        排序阶段：根据用户偏好对投票卡片排序
        
        排序因子：
        1. 创作者匹配度（是否为用户感兴趣的人）
        2. 参与度（总投票数）
        3. 新鲜度（创建时间）
        4. 随机因子（增加多样性）
        
        Args:
            current_user_id: 当前用户ID
            vote_cards: 召回的投票卡片列表
            limit: 返回数量限制
            
        Returns:
            [(vote_card, score), ...] 按分数降序排列
        """
        if not vote_cards:
            return []
        
        # 获取用户感兴趣的人
        interested_user_ids = self._get_interested_user_ids(current_user_id)
        
        scored_cards = []
        for card in vote_cards:
            score = self._calculate_vote_card_score(card, interested_user_ids)
            scored_cards.append((card, score))
        
        # 按分数降序排序
        scored_cards.sort(key=lambda x: x[1], reverse=True)
        
        return scored_cards[:limit]
    
    def _calculate_topic_card_score(
        self,
        topic_card: TopicCard,
        interested_user_ids: Set[str]
    ) -> float:
        """
        计算话题卡片相关性分数
        
        分数组成：
        - 创作者匹配度: 0-30分
        - 互动热度: 0-30分
        - 新鲜度: 0-30分
        - 随机因子: 0-10分
        
        Args:
            topic_card: 话题卡片
            interested_user_ids: 用户感兴趣的人的ID集合
            
        Returns:
            相关性分数
        """
        score = 0.0
        
        # 1. 创作者匹配度（最高30分）
        if topic_card.user_id in interested_user_ids:
            score += 30
        
        # 2. 互动热度（最高30分）
        engagement = (topic_card.discussion_count or 0) + (topic_card.like_count or 0)
        if engagement >= 100:
            score += 30
        elif engagement >= 50:
            score += 20
        elif engagement >= 10:
            score += 10
        elif engagement > 0:
            score += 5
        
        # 3. 新鲜度（最高30分）
        if topic_card.created_at:
            days_since_create = (datetime.now() - topic_card.created_at.replace(tzinfo=None)).days
            if days_since_create <= 1:
                score += 30
            elif days_since_create <= 7:
                score += 20
            elif days_since_create <= 30:
                score += 10
        
        # 4. 随机因子（0-10分，增加多样性）
        score += random.uniform(0, 10)
        
        return score
    
    def _calculate_vote_card_score(
        self,
        vote_card: VoteCard,
        interested_user_ids: Set[str]
    ) -> float:
        """
        计算投票卡片相关性分数
        
        分数组成：
        - 创作者匹配度: 0-30分
        - 参与度: 0-30分
        - 新鲜度: 0-30分
        - 随机因子: 0-10分
        
        Args:
            vote_card: 投票卡片
            interested_user_ids: 用户感兴趣的人的ID集合
            
        Returns:
            相关性分数
        """
        score = 0.0
        
        # 1. 创作者匹配度（最高30分）
        if vote_card.user_id in interested_user_ids:
            score += 30
        
        # 2. 参与度（最高30分）
        total_votes = vote_card.total_votes or 0
        if total_votes >= 100:
            score += 30
        elif total_votes >= 50:
            score += 20
        elif total_votes >= 10:
            score += 10
        elif total_votes > 0:
            score += 5
        
        # 3. 新鲜度（最高30分）
        if vote_card.created_at:
            days_since_create = (datetime.now() - vote_card.created_at.replace(tzinfo=None)).days
            if days_since_create <= 1:
                score += 30
            elif days_since_create <= 7:
                score += 20
            elif days_since_create <= 30:
                score += 10
        
        # 4. 随机因子（0-10分，增加多样性）
        score += random.uniform(0, 10)
        
        return score
    
    # ==================== 过滤工具 ====================
    
    def get_excluded_topic_card_ids(self, current_user_id: str) -> Set[str]:
        """
        获取需要排除的话题卡片ID集合
        
        包括：
        1. 用户自己创建的话题卡片
        2. 用户最近浏览过的话题卡片
        3. 用户参与讨论过的话题卡片
        
        Args:
            current_user_id: 当前用户ID
            
        Returns:
            需要排除的卡片ID集合
        """
        excluded_ids: Set[str] = set()
        
        # 1. 用户自己创建的话题卡片
        own_cards = self.db.query(TopicCard.id).filter(
            TopicCard.user_id == current_user_id
        ).all()
        excluded_ids.update([card_id[0] for card_id in own_cards])
        
        return excluded_ids
    
    def get_excluded_vote_card_ids(self, current_user_id: str) -> Set[str]:
        """
        获取需要排除的投票卡片ID集合
        
        包括：
        1. 用户自己创建的投票卡片
        2. 用户已经投过票的投票卡片
        
        Args:
            current_user_id: 当前用户ID
            
        Returns:
            需要排除的卡片ID集合
        """
        excluded_ids: Set[str] = set()
        
        # 1. 用户自己创建的投票卡片
        own_cards = self.db.query(VoteCard.id).filter(
            VoteCard.user_id == current_user_id
        ).all()
        excluded_ids.update([card_id[0] for card_id in own_cards])
        
        # 2. 用户已经投过票的投票卡片
        voted_cards = self.db.query(VoteRecord.vote_card_id).filter(
            and_(
                VoteRecord.user_id == current_user_id,
                VoteRecord.is_deleted == 0
            )
        ).distinct().all()
        excluded_ids.update([card_id[0] for card_id in voted_cards])
        
        return excluded_ids
    
    def deduplicate_cards_by_content(
        self,
        cards: List[Union[TopicCard, VoteCard]],
        similarity_threshold: float = 0.8
    ) -> List[Union[TopicCard, VoteCard]]:
        """
        基于内容语义去重
        
        简化实现：基于标题相似度进行去重
        如果两个卡片的标题相似度超过阈值，只保留一个
        
        Args:
            cards: 卡片列表
            similarity_threshold: 相似度阈值
            
        Returns:
            去重后的卡片列表
        """
        if not cards:
            return []
        
        result = []
        seen_titles = []
        
        for card in cards:
            title = card.title.lower() if card.title else ""
            is_duplicate = False
            
            for seen_title in seen_titles:
                # 简单的相似度计算：公共子串长度比例
                similarity = self._calculate_title_similarity(title, seen_title)
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                result.append(card)
                seen_titles.append(title)
        
        return result
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        计算两个标题的相似度
        
        使用简单的Jaccard相似度
        
        Args:
            title1: 标题1
            title2: 标题2
            
        Returns:
            相似度（0-1）
        """
        if not title1 or not title2:
            return 0.0
        
        # 分词（简单按字符分词）
        set1 = set(title1)
        set2 = set(title2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    # ==================== 辅助方法 ====================
    
    def _get_interested_user_ids(self, current_user_id: str) -> Set[str]:
        """
        获取用户感兴趣的人的ID集合
        
        基于：
        1. 最近访问过的用户
        
        Args:
            current_user_id: 当前用户ID
            
        Returns:
            用户ID集合
        """
        interested_ids: Set[str] = set()
        
        try:
            # 1. 最近访问过的用户
            two_weeks_ago = datetime.now() - timedelta(days=self.RECENT_VIEW_DAYS)
            recent_visits = self.db.query(UserConnection.to_user_id).filter(
                and_(
                    UserConnection.from_user_id == current_user_id,
                    UserConnection.connection_type == ConnectionType.VISIT,
                    UserConnection.updated_at >= two_weeks_ago
                )
            ).distinct().all()
            interested_ids.update([user_id[0] for user_id in recent_visits])
            
        except Exception as e:
            print(f"[TopicRecommendationService] 获取感兴趣用户失败: {str(e)}")
        
        return interested_ids
    
    def format_topic_card(
        self,
        topic_card: TopicCard,
        score: float = 0.0,
        is_recommendation: bool = True
    ) -> Dict[str, Any]:
        """
        格式化话题卡片数据
        
        Args:
            topic_card: 话题卡片对象
            score: 推荐分数
            is_recommendation: 是否为推荐卡片
            
        Returns:
            格式化的卡片数据字典
        """
        # 获取创建者信息
        creator = self.db.query(User).filter(
            User.id == topic_card.user_id
        ).first()
        
        return {
            "id": topic_card.id,
            "type": "topic",
            "card_type": "topic",
            "scene_type": "topic",
            "title": topic_card.title,
            "content": topic_card.description or topic_card.title,
            "category": topic_card.category,
            "tags": topic_card.tags or [],
            "cover_image": topic_card.cover_image,
            "images": [topic_card.cover_image] if topic_card.cover_image else [],
            "user_id": topic_card.user_id,
            "creator_id": topic_card.user_id,
            "user_avatar": creator.avatar_url if creator else '',
            "user_nickname": creator.nick_name if creator else '匿名用户',
            "like_count": topic_card.like_count or 0,
            "comment_count": topic_card.discussion_count or 0,
            "view_count": topic_card.view_count or 0,
            "is_anonymous": topic_card.is_anonymous or 0,
            "created_at": topic_card.created_at.isoformat() if topic_card.created_at else None,
            "updated_at": topic_card.updated_at.isoformat() if topic_card.updated_at else None,
            "isRecommendation": is_recommendation,
            "recommendationReason": "推荐话题" if is_recommendation else None,
            "recommend_score": round(score, 2) if score > 0 else None
        }
    
    def format_vote_card(
        self,
        vote_card: VoteCard,
        score: float = 0.0,
        is_recommendation: bool = True,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        格式化投票卡片数据
        
        Args:
            vote_card: 投票卡片对象
            score: 推荐分数
            is_recommendation: 是否为推荐卡片
            user_id: 当前用户ID（用于获取投票状态）
            
        Returns:
            格式化的卡片数据字典
        """
        # 获取创建者信息
        creator = self.db.query(User).filter(
            User.id == vote_card.user_id
        ).first()
        
        # 获取投票选项
        from app.services.vote_service import VoteService
        vote_service = VoteService(self.db)
        vote_results = vote_service.get_vote_results(vote_card.id, user_id)
        
        return {
            "id": vote_card.id,
            "type": "vote",
            "card_type": "topic",
            "scene_type": "vote",
            "vote_type": vote_card.vote_type,
            "title": vote_card.title,
            "content": vote_card.description or vote_card.title,
            "category": vote_card.category,
            "tags": vote_card.tags or [],
            "cover_image": vote_card.cover_image,
            "images": [vote_card.cover_image] if vote_card.cover_image else [],
            "user_id": vote_card.user_id,
            "creator_id": vote_card.user_id,
            "user_avatar": creator.avatar_url if creator else '',
            "user_nickname": creator.nick_name if creator else '匿名用户',
            "vote_options": vote_results["options"],
            "total_votes": vote_card.total_votes or 0,
            "has_voted": vote_results["has_voted"],
            "user_votes": vote_results["user_votes"],
            "vote_deadline": vote_card.end_time.isoformat() if vote_card.end_time else None,
            "max_selections": 1 if vote_card.vote_type == "single" else len(vote_results["options"]),
            "allow_discussion": True,
            "is_anonymous": vote_card.is_anonymous or 0,
            "created_at": vote_card.created_at.isoformat() if vote_card.created_at else None,
            "updated_at": vote_card.updated_at.isoformat() if vote_card.updated_at else None,
            "isRecommendation": is_recommendation,
            "recommendationReason": "推荐投票" if is_recommendation else None,
            "recommend_score": round(score, 2) if score > 0 else None
        }
