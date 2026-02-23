"""
推荐系统服务 - 策略层
提供召回策略、排序算法、过滤逻辑等支持服务

设计参考: vive-agent-dev-reference/产品设计/推荐设计/推荐系统第 1 版.md
"""

from typing import Optional, List, Dict, Any, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
import random

from app.models import UserConnection, ConnectionType
from app.models.user import User
from app.models.tag import Tag, UserTagRel, TagType, TagStatus, UserTagRelStatus
from app.models.user_profile import UserProfile


class RecommendationService:
    """
    推荐系统策略服务类
    
    职责：
    1. 提供各种召回策略的实现
    2. 提供排序算法实现
    3. 提供用户过滤和排除逻辑
    
    被 FeedService 调用，不直接对外暴露
    """
    
    # 推荐配置参数
    RECALL_LIMIT = 100  # 召回阶段最大数量
    RANK_LIMIT = 50     # 排序阶段输出数量
    RECENT_VIEW_DAYS = 14  # 最近浏览天数
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 召回策略 ====================
    
    def recall_by_community_tags(
        self,
        current_user_id: str,
        excluded_user_ids: Set[str] = None,
        limit: int = 30
    ) -> List[User]:
        """
        策略1: 社群用户召回
        
        召回拥有共同社群标签的用户
        例如：向所有社区成员介绍社群新人
        
        Args:
            current_user_id: 当前用户ID
            excluded_user_ids: 需要排除的用户ID集合
            limit: 召回数量限制
            
        Returns:
            召回的用户列表
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
            
            # 构建基础查询
            query = self.db.query(User).join(
                UserTagRel, User.id == UserTagRel.user_id
            ).filter(
                and_(
                    UserTagRel.tag_id.in_(tag_ids),
                    UserTagRel.user_id != current_user_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE,
                    User.is_active == True,
                    User.status != 'deleted'
                )
            )
            
            # 排除已排除的用户
            if excluded_user_ids:
                query = query.filter(~User.id.in_(excluded_user_ids))
            
            # 优先推荐新加入社群的用户（按加入时间倒序）
            users_with_same_tags = query.order_by(UserTagRel.created_at.desc()).limit(limit).all()
            
            return users_with_same_tags
            
        except Exception as e:
            print(f"[RecommendationService] 社群召回失败: {str(e)}")
            return []
    
    def recall_by_practical_purpose(
        self,
        current_user_id: str,
        excluded_user_ids: Set[str],
        limit: int = 30
    ) -> List[User]:
        """
        策略2: 实用目的召回
        
        基于对用户具体需求的理解，召回可能满足用户具体需求的用户
        此场景不需要关注对方的偏好和要求
        
        实现逻辑：
        - 根据用户的"需求标签"召回能提供对应服务的用户
        - 例如：用户需要"法律咨询"，召回有"律师"标签的用户
        
        Args:
            current_user_id: 当前用户ID
            excluded_user_ids: 需要排除的用户ID集合
            limit: 召回数量限制
            
        Returns:
            召回的用户列表
        """
        try:
            # 获取当前用户的"需求标签"（假设有特定的标签类型表示需求）
            user_needs_tags = self.db.query(UserTagRel.tag_id).filter(
                and_(
                    UserTagRel.user_id == current_user_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE
                )
            ).join(Tag, UserTagRel.tag_id == Tag.id).filter(
                Tag.tag_type == TagType.USER_PURPOSE  # 需求/目的标签
            ).all()
            
            if not user_needs_tags:
                return []
            
            tag_ids = [tag_id[0] for tag_id in user_needs_tags]
            
            # 查找拥有对应能力/服务的用户
            # 匹配逻辑：需求标签对应其他用户的能力标签
            users_with_capabilities = self.db.query(
                User,
                func.count(UserTagRel.tag_id).label('match_count')
            ).join(
                UserTagRel, User.id == UserTagRel.user_id
            ).filter(
                and_(
                    UserTagRel.tag_id.in_(tag_ids),
                    UserTagRel.user_id != current_user_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE,
                    User.is_active == True,
                    User.status != 'deleted'
                )
            ).group_by(User.id).order_by(func.count(UserTagRel.tag_id).desc()).limit(limit).all()
            
            # 过滤已排除的用户
            return [user for user, _ in users_with_capabilities if user.id not in excluded_user_ids]
            
        except Exception as e:
            print(f"[RecommendationService] 实用目的召回失败: {str(e)}")
            return []
    
    def recall_by_social_purpose(
        self,
        current_user_id: str,
        excluded_user_ids: Set[str],
        limit: int = 30
    ) -> List[User]:
        """
        策略3: 社交目的召回
        
        基于对用户偏好的理解，召回用户可能想认识以及建立连接的用户
        此场景下需要结合双方的偏好和要求
        
        实现逻辑：
        - 双向匹配：当前用户的偏好与目标用户的特征匹配
        - 同时考虑目标用户的偏好是否接受当前用户
        
        Args:
            current_user_id: 当前用户ID
            excluded_user_ids: 需要排除的用户ID集合
            limit: 召回数量限制
            
        Returns:
            召回的用户列表
        """
        try:
            # 获取当前用户的画像标签（偏好）
            user_profile_tags = self.db.query(UserTagRel.tag_id).filter(
                and_(
                    UserTagRel.user_id == current_user_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE
                )
            ).join(Tag, UserTagRel.tag_id == Tag.id).filter(
                Tag.tag_type == TagType.USER_PROFILE
            ).all()
            
            if not user_profile_tags:
                return []
            
            tag_ids = [tag_id[0] for tag_id in user_profile_tags]
            
            # 查找拥有相似画像标签的用户（双向兴趣匹配）
            users_with_similar_tags = self.db.query(
                User,
                func.count(UserTagRel.tag_id).label('match_count')
            ).join(
                UserTagRel, User.id == UserTagRel.user_id
            ).filter(
                and_(
                    UserTagRel.tag_id.in_(tag_ids),
                    UserTagRel.user_id != current_user_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE,
                    User.is_active == True,
                    User.status != 'deleted'
                )
            ).group_by(User.id).order_by(func.count(UserTagRel.tag_id).desc()).limit(limit * 2).all()
            
            # 过滤已排除的用户，并检查双向匹配
            result = []
            for user, match_count in users_with_similar_tags:
                if user.id in excluded_user_ids:
                    continue
                    
                # 检查双向匹配：目标用户是否也对当前用户感兴趣
                # 简化实现：检查目标用户是否有与当前用户匹配的画像标签
                target_user_tags = self._get_user_tag_ids(user.id, TagType.USER_PROFILE)
                current_user_tags = set(tag_ids)
                
                # 双向匹配度
                mutual_match = len(target_user_tags & current_user_tags)
                
                # 优先推荐双向匹配度高的
                if mutual_match > 0 or match_count >= 2:
                    result.append(user)
                    
                if len(result) >= limit:
                    break
            
            return result
            
        except Exception as e:
            print(f"[RecommendationService] 社交目的召回失败: {str(e)}")
            return []
    
    def recall_by_social_relations(
        self,
        current_user_id: str,
        excluded_user_ids: Set[str],
        limit: int = 20
    ) -> List[User]:
        """
        策略4: 社交关系召回
        
        召回长期未联络的朋友，展示对方动态
        
        逻辑：
        1. 优先推荐最近访问过当前用户主页的用户
        2. 推荐历史访问过但很久未访问的用户
        
        Args:
            current_user_id: 当前用户ID
            excluded_user_ids: 需要排除的用户ID集合
            limit: 召回数量限制
            
        Returns:
            召回的用户列表
        """
        try:
            two_weeks_ago = datetime.now() - timedelta(days=self.RECENT_VIEW_DAYS)
            
            # 获取最近访问过当前用户主页的用户（优先推荐）
            recent_visitors = self.db.query(User).join(
                UserConnection, User.id == UserConnection.from_user_id
            ).filter(
                and_(
                    UserConnection.to_user_id == current_user_id,
                    UserConnection.connection_type == ConnectionType.VISIT,
                    UserConnection.updated_at >= two_weeks_ago,
                    User.is_active == True,
                    User.status != 'deleted'
                )
            ).order_by(UserConnection.updated_at.desc()).limit(limit).all()
            
            # 获取历史访问过但很久未访问的用户
            old_visitors = self.db.query(User).join(
                UserConnection, User.id == UserConnection.from_user_id
            ).filter(
                and_(
                    UserConnection.to_user_id == current_user_id,
                    UserConnection.connection_type == ConnectionType.VISIT,
                    UserConnection.updated_at < two_weeks_ago,
                    User.is_active == True,
                    User.status != 'deleted'
                )
            ).order_by(UserConnection.updated_at.asc()).limit(limit).all()
            
            # 合并结果，去重
            result = []
            seen_ids = set()
            
            for user in recent_visitors + old_visitors:
                if user.id not in seen_ids and user.id not in excluded_user_ids:
                    result.append(user)
                    seen_ids.add(user.id)
                    
                if len(result) >= limit:
                    break
            
            return result
            
        except Exception as e:
            print(f"[RecommendationService] 社交关系召回失败: {str(e)}")
            return []
    
    def recall_active_users(
        self,
        current_user_id: str,
        excluded_user_ids: Set[str],
        limit: int = 50
    ) -> List[User]:
        """
        策略5: 补充召回 - 活跃用户
        
        当其他召回策略不足时，补充活跃用户
        
        Args:
            current_user_id: 当前用户ID
            excluded_user_ids: 需要排除的用户ID集合
            limit: 召回数量限制
            
        Returns:
            召回的用户列表
        """
        try:
            # 获取最近活跃的用户（按更新时间排序）
            active_users = self.db.query(User).filter(
                and_(
                    User.id != current_user_id,
                    User.is_active == True,
                    User.status != 'deleted'
                )
            ).order_by(User.updated_at.desc()).limit(limit).all()
            
            return [user for user in active_users if user.id not in excluded_user_ids]
            
        except Exception as e:
            print(f"[RecommendationService] 活跃用户召回失败: {str(e)}")
            return []
    
    # ==================== 排序策略 ====================
    
    def rank_users(
        self,
        current_user_id: str,
        users: List[User],
        limit: int
    ) -> List[Tuple[User, float]]:
        """
        排序阶段：根据用户偏好对召回结果排序
        
        排序因子：
        1. 标签匹配度（共同标签数量）
        2. 活跃度（最近更新时间）
        3. 社交关系（是否互相关注）
        4. 资料完整度
        
        Args:
            current_user_id: 当前用户ID
            users: 召回的用户列表
            limit: 返回数量限制
            
        Returns:
            [(user, score), ...] 按分数降序排列
        """
        if not users:
            return []
        
        # 获取当前用户的标签
        user_tags = self._get_user_tag_ids(current_user_id)
        
        scored_users = []
        for user in users:
            score = self._calculate_relevance_score(current_user_id, user, user_tags)
            scored_users.append((user, score))
        
        # 按分数降序排序
        scored_users.sort(key=lambda x: x[1], reverse=True)
        
        return scored_users[:limit]

    def rank_user_cards(
        self,
        current_user_id: str,
        user_cards: List['UserCard'],
        limit: int
    ) -> List[Tuple['UserCard', float]]:
        """
        排序阶段：根据用户偏好对用户名片进行排序
        
        排序因子：
        1. 标签匹配度（共同标签数量）
        2. 名片活跃度（最近更新时间）
        3. 资料完整度
        4. 随机因子（增加多样性）
        
        Args:
            current_user_id: 当前用户ID
            user_cards: 召回的用户名片列表
            limit: 返回数量限制
            
        Returns:
            [(user_card, score), ...] 按分数降序排列
        """
        if not user_cards:
            return []
        
        from app.models.user_card_db import UserCard
        
        # 获取当前用户的标签
        user_tags = self._get_user_tag_ids(current_user_id)
        
        # 获取名片对应的用户信息
        user_ids = [card.user_id for card in user_cards]
        users_map = {u.id: u for u in self.db.query(User).filter(User.id.in_(user_ids)).all()}
        
        scored_cards = []
        for card in user_cards:
            user = users_map.get(card.user_id)
            if not user:
                continue
                
            score = 0.0
            
            # 1. 标签匹配度（最高40分）
            target_user_tags = self._get_user_tag_ids(user.id)
            common_tags = user_tags & target_user_tags
            tag_match_score = min(len(common_tags) * 10, 40)
            score += tag_match_score
            
            # 2. 名片活跃度（最高30分）
            if card.updated_at:
                days_since_update = (datetime.now() - card.updated_at).days
                if days_since_update <= 1:
                    score += 30
                elif days_since_update <= 7:
                    score += 20
                elif days_since_update <= 30:
                    score += 10
            
            # 3. 资料完整度（最高20分）
            profile_score = 0
            if card.avatar_url:
                profile_score += 5
            if card.bio and len(card.bio) > 10:
                profile_score += 5
            if card.profile_data:
                if card.profile_data.get('occupation'):
                    profile_score += 5
                if card.profile_data.get('location'):
                    profile_score += 5
            score += profile_score
            
            # 4. 随机因子（0-10分，增加多样性）
            score += random.uniform(0, 10)
            
            scored_cards.append((card, score))
        
        # 按分数降序排序
        scored_cards.sort(key=lambda x: x[1], reverse=True)
        
        return scored_cards[:limit]
    
    def _calculate_relevance_score(
        self,
        current_user_id: str,
        target_user: User,
        current_user_tags: Set[int]
    ) -> float:
        """
        计算用户相关性分数
        
        分数组成：
        - 标签匹配度: 0-40分
        - 活跃度: 0-30分
        - 资料完整度: 0-20分
        - 随机因子: 0-10分（增加多样性）
        
        Args:
            current_user_id: 当前用户ID
            target_user: 目标用户
            current_user_tags: 当前用户的标签ID集合
            
        Returns:
            相关性分数
        """
        score = 0.0
        
        # 1. 标签匹配度（最高40分）
        target_user_tags = self._get_user_tag_ids(target_user.id)
        common_tags = current_user_tags & target_user_tags
        tag_match_score = min(len(common_tags) * 10, 40)
        score += tag_match_score
        
        # 2. 活跃度（最高30分）
        if target_user.updated_at:
            days_since_update = (datetime.now() - target_user.updated_at).days
            if days_since_update <= 1:
                score += 30
            elif days_since_update <= 7:
                score += 20
            elif days_since_update <= 30:
                score += 10
        
        # 3. 资料完整度（最高20分）
        profile_score = 0
        if target_user.avatar_url:
            profile_score += 5
        if target_user.bio and len(target_user.bio) > 10:
            profile_score += 5
        if target_user.occupation:
            profile_score += 5
        if target_user.location:
            profile_score += 5
        score += profile_score
        
        # 4. 随机因子（0-10分，增加多样性）
        score += random.uniform(0, 10)
        
        return score
    
    # ==================== 过滤工具 ====================
    
    def get_excluded_user_ids(self, current_user_id: str) -> Set[str]:
        """
        获取需要排除的用户ID集合
        
        包括：
        1. 当前用户自己
        2. 最近浏览过的用户
        3. 已建立连接的用户
        4. 被拉黑的用户
        
        Args:
            current_user_id: 当前用户ID
            
        Returns:
            需要排除的用户ID集合
        """
        excluded_ids: Set[str] = {current_user_id}
        
        # 获取最近浏览过的用户（VIEW类型）
        two_weeks_ago = datetime.now() - timedelta(days=self.RECENT_VIEW_DAYS)
        recent_viewed = self.db.query(UserConnection.to_user_id).filter(
            and_(
                UserConnection.from_user_id == current_user_id,
                UserConnection.connection_type == ConnectionType.VIEW,
                UserConnection.updated_at >= two_weeks_ago
            )
        ).distinct().all()
        excluded_ids.update([user_id[0] for user_id in recent_viewed])
        
        # 获取已建立连接的用户
        connections = self.db.query(UserConnection).filter(
            or_(
                UserConnection.from_user_id == current_user_id,
                UserConnection.to_user_id == current_user_id
            )
        ).all()
        
        for conn in connections:
            if conn.from_user_id == current_user_id:
                excluded_ids.add(conn.to_user_id)
            else:
                excluded_ids.add(conn.from_user_id)
        
        return excluded_ids
    
    def apply_filters(
        self,
        users: List[User],
        filters: Dict[str, Any]
    ) -> List[User]:
        """
        应用过滤条件
        
        支持的过滤条件：
        - gender: 性别筛选
        - city: 城市筛选
        - age_range: 年龄范围 [min, max]
        
        Args:
            users: 用户列表
            filters: 过滤条件字典
            
        Returns:
            过滤后的用户列表
        """
        filtered_users = users
        
        if 'gender' in filters and filters['gender']:
            filtered_users = [u for u in filtered_users if u.gender == filters['gender']]
        
        if 'city' in filters and filters['city']:
            filtered_users = [
                u for u in filtered_users 
                if u.location and filters['city'] in u.location
            ]
        
        return filtered_users
    
    # ==================== 辅助方法 ====================
    
    def _get_user_tag_ids(self, user_id: str, tag_type: Optional[TagType] = None) -> Set[int]:
        """
        获取用户的标签ID集合
        
        Args:
            user_id: 用户ID
            tag_type: 标签类型筛选（可选）
            
        Returns:
            标签ID集合
        """
        try:
            query = self.db.query(UserTagRel.tag_id).filter(
                and_(
                    UserTagRel.user_id == user_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE
                )
            )
            
            if tag_type:
                query = query.join(Tag, UserTagRel.tag_id == Tag.id).filter(
                    Tag.tag_type == tag_type
                )
            
            tag_rels = query.all()
            return set(tag_id[0] for tag_id in tag_rels)
        except Exception:
            return set()
    
    def format_recommended_user(
        self,
        user: User,
        current_user_id: str,
        score: float
    ) -> Dict[str, Any]:
        """
        格式化推荐用户数据
        
        Args:
            user: 用户对象
            current_user_id: 当前用户ID
            score: 推荐分数
            
        Returns:
            格式化的用户数据字典
        """
        # 获取用户标签
        user_tags = self.db.query(Tag).join(
            UserTagRel, Tag.id == UserTagRel.tag_id
        ).filter(
            and_(
                UserTagRel.user_id == user.id,
                UserTagRel.status == UserTagRelStatus.ACTIVE,
                Tag.status == TagStatus.ACTIVE
            )
        ).limit(5).all()
        
        # 获取用户画像摘要
        user_profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user.id
        ).first()
        
        # 检查连接状态
        connection = self.db.query(UserConnection).filter(
            or_(
                and_(
                    UserConnection.from_user_id == current_user_id,
                    UserConnection.to_user_id == user.id
                ),
                and_(
                    UserConnection.from_user_id == user.id,
                    UserConnection.to_user_id == current_user_id
                )
            )
        ).first()
        
        return {
            "id": user.id,
            "nick_name": user.nick_name,
            "avatar_url": user.avatar_url,
            "gender": user.gender,
            "occupation": user.occupation,
            "location": user.location,
            "bio": user.bio,
            "tags": [{"id": tag.id, "name": tag.name} for tag in user_tags],
            "profile_summary": user_profile.profile_summary if user_profile else None,
            "recommend_score": round(score, 2),
            "connection_status": connection.status.value if connection else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
