from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ContentType(enum.Enum):
    """内容类型枚举"""
    CARD = "card"           # 用户卡片
    TOPIC = "topic"         # 话题
    ARTICLE = "article"     # 文章
    LINK = "link"           # 链接


class ContentStatus(enum.Enum):
    """内容状态枚举"""
    DRAFT = "draft"         # 草稿
    PUBLISHED = "published" # 已发布
    ARCHIVED = "archived"   # 已归档


class TagContent(Base):
    """标签推送内容模型"""
    __tablename__ = "tag_contents"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    title = Column(String(100), nullable=False, comment="内容标题")
    content = Column(Text, nullable=False, comment="内容详情")
    content_type = Column(Enum(ContentType), nullable=False, comment="内容类型")
    target_id = Column(String(36), nullable=True, comment="关联目标ID（如用户卡片ID）")
    cover_image = Column(String(500), default='', comment="封面图URL")
    tag_ids = Column(JSON, nullable=False, comment="关联的标签ID列表")
    priority = Column(Integer, default=0, comment="推送优先级，数值越大越优先")
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT, comment="状态")
    view_count = Column(Integer, default=0, comment="浏览次数")
    like_count = Column(Integer, default=0, comment="点赞次数")
    share_count = Column(Integer, default=0, comment="分享次数")
    created_by = Column(String(36), nullable=False, index=True, comment="创建者用户ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    published_at = Column(DateTime(timezone=True), nullable=True, comment="发布时间")
    
    # 索引
    __table_args__ = (
        Index('idx_content_type', 'content_type'),
        Index('idx_content_status', 'status'),
        Index('idx_content_created_by', 'created_by'),
    )


class ContentTagInteraction(Base):
    """内容和标签的交互记录"""
    __tablename__ = "content_tag_interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    content_id = Column(Integer, nullable=False, index=True, comment="内容ID")
    user_id = Column(String(36), nullable=False, index=True, comment="用户ID")
    interaction_type = Column(String(20), nullable=False, comment="交互类型：view/like/share")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="交互时间")
    
    # 索引
    __table_args__ = (
        Index('idx_interaction_content', 'content_id'),
        Index('idx_interaction_user', 'user_id'),
    )
