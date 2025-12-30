from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import math

from app.models.user import User
from app.models.user_card_db import UserCard
from app.models.vote_card_db import VoteCard
from app.models.topic_card_db import TopicCard


class PointsService:
    """积分管理服务"""
    
    # 积分配置
    POINTS_CONFIG = {
        # 积分获取规则
        'earn': {
            'complete_survey': 10,      # 完成问卷奖励
            'daily_login': 2,           # 每日登录奖励
            'share_card': 5,            # 分享卡片奖励
            'invite_friend': 20,        # 邀请好友奖励
            'vote_participation': 50,   # 投票参与奖励
            'discussion_participation': 50,  # 讨论参与奖励
        },
        # 积分消耗规则
        'consume': {
            'create_user_card': 100,    # 创建身份卡片消耗
            'create_vote_card': 100,    # 创建投票卡片消耗
            'create_topic_card': 100,   # 创建话题卡片消耗
        },
        # 等级配置
        'level_config': {
            'base_points': 100,         # 每级基础积分
            'growth_factor': 1.5,       # 等级增长因子
            'max_level': 50,            # 最高等级
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_points_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户积分信息"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")
        
        return {
            'user_id': user.id,
            'points': user.points,
            'level': user.level,
            'level_progress': self._calculate_level_progress(user.points, user.level),
            'next_level_points': self._calculate_level_requirement(user.level + 1),
            'level_title': self._get_level_title(user.level)
        }
    
    def add_points(self, user_id: str, points: int, reason: str = "") -> Dict[str, Any]:
        """增加用户积分"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")
        
        old_points = user.points
        user.points += points
        
        # 检查等级升级
        old_level = user.level
        new_level = self._calculate_level(user.points)
        level_up = False
        
        if new_level > old_level:
            user.level = new_level
            level_up = True
        
        self.db.commit()
        
        return {
            'success': True,
            'user_id': user_id,
            'points_added': points,
            'old_points': old_points,
            'new_points': user.points,
            'old_level': old_level,
            'new_level': new_level,
            'level_up': level_up,
            'reason': reason
        }
    
    def consume_points(self, user_id: str, points: int, reason: str = "") -> Dict[str, Any]:
        """消耗用户积分"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")
        
        if user.points < points:
            return {
                'success': False,
                'user_id': user_id,
                'current_points': user.points,
                'required_points': points,
                'reason': reason,
                'message': '积分不足'
            }
        
        old_points = user.points
        user.points -= points
        self.db.commit()
        
        return {
            'success': True,
            'user_id': user_id,
            'points_consumed': points,
            'old_points': old_points,
            'new_points': user.points,
            'reason': reason
        }
    
    def reward_survey_completion(self, user_id: str) -> Dict[str, Any]:
        """奖励问卷完成"""
        points = self.POINTS_CONFIG['earn']['complete_survey']
        return self.add_points(user_id, points, "完成问卷奖励")
    
    def reward_vote_participation(self, user_id: str) -> Dict[str, Any]:
        """奖励投票参与"""
        points = self.POINTS_CONFIG['earn']['vote_participation']
        return self.add_points(user_id, points, "投票参与奖励")
    
    def reward_discussion_participation(self, user_id: str) -> Dict[str, Any]:
        """奖励讨论参与"""
        points = self.POINTS_CONFIG['earn']['discussion_participation']
        return self.add_points(user_id, points, "讨论参与奖励")
    
    def consume_create_card(self, user_id: str, card_type: str) -> Dict[str, Any]:
        """消耗创建卡片的积分"""
        if card_type not in ['user_card', 'vote_card', 'topic_card']:
            raise ValueError("无效的卡片类型")
        
        consume_key = f"create_{card_type}"
        points = self.POINTS_CONFIG['consume'][consume_key]
        return self.consume_points(user_id, points, f"创建{self._get_card_type_name(card_type)}")
    
    def check_create_card_permission(self, user_id: str, card_type: str) -> Dict[str, Any]:
        """检查创建卡片权限"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")
        
        if card_type not in ['user_card', 'vote_card', 'topic_card']:
            raise ValueError("无效的卡片类型")
        
        consume_key = f"create_{card_type}"
        required_points = self.POINTS_CONFIG['consume'][consume_key]
        
        return {
            'can_create': user.points >= required_points,
            'current_points': user.points,
            'required_points': required_points,
            'card_type': card_type,
            'card_type_name': self._get_card_type_name(card_type)
        }
    
    def _calculate_level(self, points: int) -> int:
        """根据积分计算等级"""
        base_points = self.POINTS_CONFIG['level_config']['base_points']
        growth_factor = self.POINTS_CONFIG['level_config']['growth_factor']
        max_level = self.POINTS_CONFIG['level_config']['max_level']
        
        level = 1
        while level < max_level:
            level_requirement = self._calculate_level_requirement(level + 1)
            if points >= level_requirement:
                level += 1
            else:
                break
        
        return level
    
    def _calculate_level_requirement(self, level: int) -> int:
        """计算等级要求积分"""
        if level <= 1:
            return 0
        
        base_points = self.POINTS_CONFIG['level_config']['base_points']
        growth_factor = self.POINTS_CONFIG['level_config']['growth_factor']
        
        # 使用指数增长公式：基础积分 * (增长因子 ^ (等级-1))
        return int(base_points * (growth_factor ** (level - 1)))
    
    def _calculate_level_progress(self, points: int, level: int) -> float:
        """计算当前等级进度百分比"""
        if level >= self.POINTS_CONFIG['level_config']['max_level']:
            return 100.0
        
        current_level_requirement = self._calculate_level_requirement(level)
        next_level_requirement = self._calculate_level_requirement(level + 1)
        
        if next_level_requirement <= current_level_requirement:
            return 100.0
        
        progress = (points - current_level_requirement) / (next_level_requirement - current_level_requirement) * 100
        return min(100.0, max(0.0, progress))
    
    def _get_level_title(self, level: int) -> str:
        """获取等级称号"""
        return f"Lv{level}"
    
    def _get_card_type_name(self, card_type: str) -> str:
        """获取卡片类型名称"""
        names = {
            'user_card': '身份卡片',
            'vote_card': '投票卡片',
            'topic_card': '话题卡片'
        }
        return names.get(card_type, '未知卡片')