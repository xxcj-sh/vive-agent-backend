from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

class UserCard(Base):
    """用户角色资料数据库模型"""
    __tablename__ = "user_cards"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    role_type = Column(String(50), nullable=False)
    scene_type = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    trigger_and_output = Column(Text, nullable=True)
    profile_data = Column(JSON, nullable=True)
    preferences = Column(JSON, nullable=True)
    visibility = Column(String(20), default="public")
    is_active = Column(Integer, default=1)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    search_code = Column(String(100), nullable=True, index=True)
    
    # 关系
    user = relationship("User", back_populates="cards")
