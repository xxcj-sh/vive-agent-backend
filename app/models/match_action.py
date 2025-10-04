from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, UniqueConstraint, Index, Text
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
    AI_RECOMMEND_BY_SYSTEM = "ai_recommend_by_system"  # 系统主动 AI 引荐
    COLLECTION = "collection"  # 收藏卡片
    FOLLOW = "follow"          # 关注
    FOLLOW_AFTER_TRIGGER_IN_CHAT = "follow_after_trigger_in_chat"  # 触发后在聊天中关注

class MatchResultStatus(str, enum.Enum):
    """匹配结果状态枚举"""
    PENDING = "pending"        # 等待对方操作
    MATCHED = "matched"        # 双向匹配成功
    UNMATCHED = "unmatched"    # 未匹配
    EXPIRED = "expired"        # 已过期
    BLOCKED = "blocked"        # 已屏蔽

class MatchAction(Base):
    """用户匹配操作记录表"""
    __tablename__ = "match_actions"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # 操作用户ID
    target_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # 目标用户ID
    target_card_id = Column(String(36), nullable=False)  # 目标卡片ID
    action_type = Column(Enum(MatchActionType), nullable=False)  # 操作类型
    scene_type = Column(String(50), nullable=False)  # 匹配场景类型 (socail/activity)
    scene_context = Column(Text, nullable=True)  # 场景上下文信息（扩展为Text类型）
    source = Column(String(20), default="user")  # 操作来源：user/system/ai
    is_processed = Column(Boolean, default=False)  # 是否已处理（用于异步任务）
    processed_at = Column(DateTime(timezone=True), nullable=True)  # 处理完成时间
    extra = Column(Text, nullable=True)  # 额外元数据（JSON格式）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 添加复合索引优化查询性能
    __table_args__ = (
        UniqueConstraint('user_id', 'target_user_id', 'target_card_id', 'scene_type', 
                        name='unique_user_target_action'),
        Index('idx_user_scene_created', 'user_id', 'scene_type', 'created_at'),
        Index('idx_target_user_scene', 'target_user_id', 'scene_type', 'created_at'),
        Index('idx_action_type_scene', 'action_type', 'scene_type'),
        Index('idx_created_at', 'created_at'),
        Index('idx_source_processed', 'source', 'is_processed'),
    )
    
    # 关系
    user = relationship("User", foreign_keys=[user_id], backref="match_actions_made")
    target_user = relationship("User", foreign_keys=[target_user_id], backref="match_actions_received")

class MatchResult(Base):
    """匹配结果记录表"""
    __tablename__ = "match_results"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user1_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # 用户1 ID
    user2_id = Column(String(36), ForeignKey("users.id"), nullable=False)  # 用户2 ID
    user1_card_id = Column(String(36), nullable=False)  # 用户1的卡片ID
    user2_card_id = Column(String(36), nullable=False)  # 用户2的卡片ID
    scene_type = Column(String(50), nullable=False)  # 匹配场景类型
    status = Column(Enum(MatchResultStatus), default=MatchResultStatus.MATCHED)  # 匹配状态
    user1_action_id = Column(String(36), ForeignKey("match_actions.id"), nullable=False)  # 用户1的操作记录ID
    user2_action_id = Column(String(36), ForeignKey("match_actions.id"), nullable=False)  # 用户2的操作记录ID
    matched_at = Column(DateTime(timezone=True), server_default=func.now())  # 匹配成功时间
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())  # 最后活动时间

    is_active = Column(Boolean, default=True)  # 是否活跃
    is_blocked = Column(Boolean, default=False)  # 是否被屏蔽
    expiry_date = Column(DateTime(timezone=True), nullable=True)  # 过期时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 添加复合索引优化查询性能
    __table_args__ = (
        UniqueConstraint('user1_id', 'user2_id', 'scene_type', 
                        name='unique_user_pair_match'),
        Index('idx_user1_scene_active', 'user1_id', 'scene_type', 'is_active'),
        Index('idx_user2_scene_active', 'user2_id', 'scene_type', 'is_active'),
        Index('idx_status_active', 'status', 'is_active'),
        Index('idx_matched_at', 'matched_at'),
        Index('idx_last_activity', 'last_activity_at'),
        Index('idx_expiry_date', 'expiry_date'),
    )
    
    # 关系
    user1 = relationship("User", foreign_keys=[user1_id], backref="match_results_as_user1")
    user2 = relationship("User", foreign_keys=[user2_id], backref="match_results_as_user2")
    user1_action = relationship("MatchAction", foreign_keys=[user1_action_id])
    user2_action = relationship("MatchAction", foreign_keys=[user2_action_id])