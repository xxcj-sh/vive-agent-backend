from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class VoteCard(Base):
    """投票卡片数据库模型"""
    __tablename__ = "vote_cards"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(200), nullable=False, comment="投票标题")
    description = Column(Text, nullable=True, comment="投票描述")
    category = Column(String(50), nullable=True, comment="投票分类")
    tags = Column(JSON, nullable=True, comment="投票标签")
    cover_image = Column(String(500), nullable=True, comment="封面图片URL")
    vote_type = Column(String(20), default="single", comment="投票类型: single(单选), multiple(多选)")
    is_anonymous = Column(Integer, default=0, comment="是否匿名投票")
    is_realtime_result = Column(Integer, default=1, comment="是否实时显示结果")
    is_active = Column(Integer, default=1, comment="是否激活")
    is_deleted = Column(Integer, default=0, comment="是否删除")
    visibility = Column(String(20), default="public", comment="可见性: public, private")
    view_count = Column(Integer, default=0, comment="浏览次数")
    total_votes = Column(Integer, default=0, comment="总投票数")
    discussion_count = Column(Integer, default=0, comment="讨论次数")
    share_count = Column(Integer, default=0, comment="分享次数")
    start_time = Column(DateTime(timezone=True), nullable=True, comment="投票开始时间")
    end_time = Column(DateTime(timezone=True), nullable=True, comment="投票结束时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="vote_cards")
    vote_options = relationship("VoteOption", back_populates="vote_card", cascade="all, delete-orphan")
    vote_records = relationship("VoteRecord", back_populates="vote_card", cascade="all, delete-orphan")
    discussions = relationship("VoteDiscussion", back_populates="vote_card", cascade="all, delete-orphan")
    user_card_relations = relationship("UserCardVoteRelation", back_populates="vote_card", cascade="all, delete-orphan")

class VoteOption(Base):
    """投票选项数据库模型"""
    __tablename__ = "vote_options"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    vote_card_id = Column(String(36), ForeignKey("vote_cards.id"), index=True, nullable=False)
    option_text = Column(String(500), nullable=False, comment="选项文本")
    option_image = Column(String(500), nullable=True, comment="选项图片URL")
    vote_count = Column(Integer, default=0, comment="该选项的投票数")
    display_order = Column(Integer, default=0, comment="显示顺序")
    is_active = Column(Integer, default=1, comment="是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    vote_card = relationship("VoteCard", back_populates="vote_options")

class VoteRecord(Base):
    """投票记录数据库模型"""
    __tablename__ = "vote_records"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    vote_card_id = Column(String(36), ForeignKey("vote_cards.id"), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    option_id = Column(String(36), ForeignKey("vote_options.id"), index=True, nullable=False)
    is_anonymous = Column(Integer, default=0, comment="是否匿名投票")
    is_deleted = Column(Integer, default=0, comment="是否删除")
    ip_address = Column(String(50), nullable=True, comment="投票者IP地址")
    user_agent = Column(String(500), nullable=True, comment="用户代理信息")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    vote_card = relationship("VoteCard", back_populates="vote_records")
    user = relationship("User", back_populates="vote_records")
    vote_option = relationship("VoteOption")

class VoteDiscussion(Base):
    """投票讨论记录数据库模型"""
    __tablename__ = "vote_discussions"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    vote_card_id = Column(String(36), ForeignKey("vote_cards.id"), index=True, nullable=False)
    participant_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    host_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    message = Column(Text, nullable=False, comment="讨论消息内容")
    message_type = Column(String(20), default="text", comment="消息类型: text, image, voice")
    is_anonymous = Column(Integer, default=1, comment="是否匿名")
    is_deleted = Column(Integer, default=0, comment="是否删除")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    vote_card = relationship("VoteCard", back_populates="discussions")
    participant = relationship("User", foreign_keys=[participant_id], back_populates="vote_discussions_as_participant")
    host = relationship("User", foreign_keys=[host_id], back_populates="vote_discussions_as_host")

class UserCardVoteRelation(Base):
    """用户卡片与投票卡片的关联关系表"""
    __tablename__ = "user_card_vote_relations"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    vote_card_id = Column(String(36), ForeignKey("vote_cards.id"), index=True, nullable=False)
    relation_type = Column(String(20), nullable=False, comment="关系类型: created(创建), participated(参与)")
    is_active = Column(Integer, default=1, comment="是否激活")
    is_deleted = Column(Integer, default=0, comment="是否删除")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="vote_relations")
    vote_card = relationship("VoteCard", back_populates="user_card_relations")