from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.user import User
import uuid

class TopicCard(Base):
    """话题卡片数据库模型"""
    __tablename__ = "topic_cards"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(200), nullable=False, comment="话题标题")
    description = Column(Text, nullable=True, comment="话题描述")
    discussion_goal = Column(Text, nullable=True, comment="讨论目标/期待")
    category = Column(String(50), nullable=True, comment="话题分类")
    tags = Column(JSON, nullable=True, comment="话题标签")
    cover_image = Column(String(500), nullable=True, comment="封面图片URL")
    is_active = Column(Integer, default=1, comment="是否激活")
    is_deleted = Column(Integer, default=0, comment="是否删除")
    is_anonymous = Column(Integer, default=0, comment="是否匿名")
    visibility = Column(String(20), default="public", comment="可见性: public, private")
    view_count = Column(Integer, default=0, comment="浏览次数")
    like_count = Column(Integer, default=0, comment="点赞次数")
    discussion_count = Column(Integer, default=0, comment="讨论次数")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="topic_cards")
    discussions = relationship("TopicDiscussion", back_populates="topic_card", cascade="all, delete-orphan")
    trigger_conditions = relationship("TopicTriggerCondition", back_populates="topic_card", cascade="all, delete-orphan")
    user_card_relations = relationship("UserCardTopicRelation", back_populates="topic_card", cascade="all, delete-orphan")

class TopicDiscussion(Base):
    """话题讨论记录数据库模型"""
    __tablename__ = "topic_discussions"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    topic_card_id = Column(String(36), ForeignKey("topic_cards.id"), index=True, nullable=False)
    participant_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    host_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    message = Column(Text, nullable=False, comment="讨论消息内容")
    message_type = Column(String(20), default="text", comment="消息类型: text, image, voice")
    is_anonymous = Column(Integer, default=1, comment="是否匿名")
    is_deleted = Column(Integer, default=0, comment="是否删除")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    topic_card = relationship("TopicCard", back_populates="discussions")
    participant = relationship("User", foreign_keys=[participant_id], back_populates="topic_discussions_as_participant")
    host = relationship("User", foreign_keys=[host_id], back_populates="topic_discussions_as_host")

class TopicTriggerCondition(Base):
    """话题触发条件数据库模型"""
    __tablename__ = "topic_trigger_conditions"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    topic_card_id = Column(String(36), ForeignKey("topic_cards.id"), index=True, nullable=False)
    trigger_type = Column(String(50), default="basic", comment="触发条件类型: basic, smart, time, location")
    trigger_content = Column(Text, nullable=True, comment="触发词内容")
    output_content = Column(Text, nullable=True, comment="回复内容/讨论目标")
    confidence = Column(String(20), default="medium", comment="智能匹配置信度: high, medium, low")
    time_type = Column(String(20), nullable=True, comment="时间类型: fixed, range, periodic")
    start_time = Column(String(20), nullable=True, comment="开始时间")
    end_time = Column(String(20), nullable=True, comment="结束时间")
    location_type = Column(String(20), nullable=True, comment="位置类型: specific, area")
    location_data = Column(JSON, nullable=True, comment="位置数据")
    frequency_limit = Column(Integer, default=0, comment="频率限制，0表示无限制")
    is_active = Column(Integer, default=1, comment="是否激活")
    priority = Column(Integer, default=1, comment="优先级，数字越大优先级越高")
    extra_config = Column(JSON, nullable=True, comment="额外配置信息")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    topic_card = relationship("TopicCard", back_populates="trigger_conditions")


class UserCardTopicRelation(Base):
    """用户卡片与话题卡片的关联关系表"""
    __tablename__ = "user_card_topic_relations"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_card_id = Column(String(36), ForeignKey("user_cards.id"), index=True, nullable=False)
    topic_card_id = Column(String(36), ForeignKey("topic_cards.id"), index=True, nullable=False)
    relation_type = Column(String(20), nullable=False, comment="关系类型: created(创建), interested(感兴趣)")
    is_active = Column(Integer, default=1, comment="是否激活")
    is_deleted = Column(Integer, default=0, comment="是否删除")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user_card = relationship("UserCard", back_populates="topic_relations")
    topic_card = relationship("TopicCard", back_populates="user_card_relations")