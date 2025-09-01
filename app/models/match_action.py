from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.db_config import Base
import enum
import uuid

class MatchActionType(str, enum.Enum):
    """匹配操作类型枚举"""
    LIKE = "like"              # 喜欢
    DISLIKE = "dislike"        # 不喜欢
    SUPER_LIKE = "super_like"  # 超级喜欢
    PASS = "pass"              # 跳过

class MatchResultStatus(str, enum.Enum):
    """匹配结果状态枚举"""
    PENDING = "pending"        # 等待对方操作
    MATCHED = "matched"        # 双向匹配成功
    UNMATCHED = "unmatched"    # 未匹配
    EXPIRED = "expired"        # 已过期

class MatchAction(Base):
    """用户匹配操作记录表"""
    __tablename__ = "match_actions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 操作用户ID
    target_user_id = Column(String, ForeignKey("users.id"), nullable=False)  # 目标用户ID
    target_card_id = Column(String, nullable=False)  # 目标卡片ID（可能是用户资料ID或房源ID等）
    action_type = Column(Enum(MatchActionType), nullable=False)  # 操作类型
    match_type = Column(String, nullable=False)  # 匹配场景类型 (housing/dating/activity)
    scene_context = Column(String, nullable=True)  # 场景上下文信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 添加唯一约束，防止同一用户对同一目标重复操作
    __table_args__ = (
        UniqueConstraint('user_id', 'target_user_id', 'target_card_id', 'match_type', 
                        name='unique_user_target_action'),
    )
    
    # 关系
    user = relationship("User", foreign_keys=[user_id], backref="match_actions_made")
    target_user = relationship("User", foreign_keys=[target_user_id], backref="match_actions_received")

class MatchResult(Base):
    """匹配结果记录表"""
    __tablename__ = "match_results"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user1_id = Column(String, ForeignKey("users.id"), nullable=False)  # 用户1 ID
    user2_id = Column(String, ForeignKey("users.id"), nullable=False)  # 用户2 ID
    user1_card_id = Column(String, nullable=False)  # 用户1的卡片ID
    user2_card_id = Column(String, nullable=False)  # 用户2的卡片ID
    match_type = Column(String, nullable=False)  # 匹配场景类型
    status = Column(Enum(MatchResultStatus), default=MatchResultStatus.MATCHED)  # 匹配状态
    user1_action_id = Column(String, ForeignKey("match_actions.id"), nullable=False)  # 用户1的操作记录ID
    user2_action_id = Column(String, ForeignKey("match_actions.id"), nullable=False)  # 用户2的操作记录ID
    matched_at = Column(DateTime(timezone=True), server_default=func.now())  # 匹配成功时间
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())  # 最后活动时间
    is_active = Column(Boolean, default=True)  # 是否活跃
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 添加唯一约束，确保两个用户之间在同一场景下只有一个匹配结果
    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', 'match_type', 
                        name='unique_user_pair_match'),
    )
    
    # 关系
    user1 = relationship("User", foreign_keys=[user1_id], backref="match_results_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], backref="match_results_as_user2")
    user1_action = relationship("MatchAction", foreign_keys=[user1_action_id])
    user2_action = relationship("MatchAction", foreign_keys=[user2_action_id])