from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
import json

# 可见性常量
VISIBILITY_PUBLIC = "public"
VISIBILITY_PRIVATE = "private"

class UserCard(Base):
    """用户身份卡片数据库模型"""
    __tablename__ = "user_cards"

    # 微信小程序码支持的参数最大为 32 个可见字符，如果想要为每一张卡片创建一个二维码，需要将卡片的 ID 长度控制在 32 个字符以内。
    id = Column(String(32), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    role_type = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    preferences = Column(String, nullable=True)
    visibility = Column(String(20), default="public")  # public, private
    is_active = Column(Integer, default=1)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    search_code = Column(String(100), nullable=True, index=True)
    
    # 关系
    user = relationship("User", back_populates="cards")
    # topic_relations = relationship("UserCardTopicRelation", back_populates="user_card", cascade="all, delete-orphan")
    
    def to_dict(self, include_private=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "role_type": self.role_type,
            "visibility": self.visibility,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "search_code": self.search_code
        }

        # 私有模式处理
        if self.visibility == VISIBILITY_PRIVATE and not include_private:
            # 私有模式下不暴露详细信息
            data["display_name"] = "私有用户"
            data["avatar_url"] = ""
            data["bio"] = ""
            data["preferences"] = ""
        else:
            data["display_name"] = self.display_name
            data["avatar_url"] = self.avatar_url
            data["bio"] = self.bio
            data["preferences"] = self.preferences or ""

        return data
