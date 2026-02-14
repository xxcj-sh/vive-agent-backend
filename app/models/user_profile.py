"""
用户画像数据模型
用于存储LLM生成的用户画像数据
"""

from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
import uuid
import json

try:
    from sqlalchemy.dialects.mysql import VECTOR
    VECTOR_TYPE_AVAILABLE = True
except ImportError:
    VECTOR = None
    VECTOR_TYPE_AVAILABLE = False


VECTOR_DIMENSION = 1024


def get_embedding_column():
    """获取向量列，根据 SQLAlchemy 版本选择合适的类型"""
    if VECTOR_TYPE_AVAILABLE:
        return Column(VECTOR(VECTOR_DIMENSION), nullable=True, comment=f"用户画像语义向量（{VECTOR_DIMENSION}维，豆包模型生成）")
    else:
        return Column(Text, nullable=True, comment=f"用户画像语义向量（{VECTOR_DIMENSION}维，JSON格式存储）")


class UserProfile(Base):
    """用户画像数据表"""
    __tablename__ = "user_profiles"

    id = Column(String(64), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(64), nullable=False, index=True, comment="用户ID")

    # 原始画像数据 - 存储LLM生成的完整用户画像
    raw_profile = Column(Text, nullable=True, comment="原始用户画像数据（JSON格式）")

    # 用户画像语义向量 - 使用阿里云 RDS MySQL VECTOR 类型
    raw_profile_embedding = get_embedding_column()

    # 生成的总结文本 - LLM生成的自然语言用户画像描述（可直接阅读的文本）
    profile_summary = Column(Text, nullable=True, comment="用户画像总结文本（LLM生成的可读文本）")

    # 更新原因和时间戳
    update_reason = Column(String(500), nullable=True, comment="更新原因")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    # 关联关系 - 使用字符串引用避免循环导入
    history = relationship("UserProfileHistory", back_populates="profile", cascade="all, delete-orphan", lazy="selectin")

    # 向量索引 - 使用 HNSW 算法，支持余弦距离检索
    # 注意：阿里云 RDS MySQL 使用 VECTOR INDEX 语法，需通过迁移脚本创建
    # 示例 SQL: VECTOR INDEX idx_embedding(raw_profile_embedding) M=16 DISTANCE=COSINE


# Pydantic 模型用于API
class UserProfileBase(BaseModel):
    """用户画像基础模型"""
    user_id: str = Field(..., description="用户ID")
    raw_profile: Optional[str] = Field(None, description="原始用户画像数据（JSON格式）")
    raw_profile_embedding: Any = Field(None, description="用户画像语义向量（1024维，豆包模型生成）")
    profile_summary: Optional[str] = Field(None, description="用户画像总结文本（LLM生成的可读文本）")
    update_reason: Optional[str] = Field(None, description="更新原因")
    
    @field_validator('raw_profile_embedding')
    @classmethod
    def validate_embedding(cls, v):
        """将任何类型的 embedding 转换为字符串或 None"""
        if v is None:
            return None
        if isinstance(v, str):
            return v
        try:
            return str(v)
        except Exception:
            return None


class UserProfileCreate(UserProfileBase):
    """创建用户画像模型"""
    pass


class UserProfileUpdate(BaseModel):
    """更新用户画像模型"""
    raw_profile: Optional[str] = Field(None, description="原始用户画像数据（JSON格式）")
    profile_summary: Optional[str] = Field(None, description="用户画像总结文本（LLM生成的可读文本）")
    update_reason: Optional[str] = Field(None, description="更新原因")


class UserProfileResponse(UserProfileBase):
    """用户画像响应模型"""
    id: str = Field(..., description="画像ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class UserProfileListResponse(BaseModel):
    """用户画像列表响应模型"""
    profiles: list[UserProfileResponse] = Field(..., description="用户画像列表")
    total_count: int = Field(..., description="总数量")


def run_migration(db_session):
    """
    执行数据库迁移
    确保 user_profiles 表存在且字段约束正确
    """
    from sqlalchemy import text
    
    try:
        result = db_session.execute(text("SHOW TABLES LIKE 'user_profiles'"))
        if result.fetchone():
            print("user_profiles 表已存在")
        else:
            print("user_profiles 表不存在，需要创建")
            
        migrate_raw_profile_embedding(db_session)
        
    except Exception as e:
        print(f"数据库迁移失败: {str(e)}")
        raise


def migrate_raw_profile_embedding(db_session):
    """
    迁移 raw_profile_embedding 字段，允许为 NULL
    MySQL VECTOR 类型要求 NOT NULL，如果需要支持 NULL 需要改用 TEXT 类型
    """
    from sqlalchemy import text
    
    try:
        result = db_session.execute(text("""
            SELECT IS_NULLABLE, COLUMN_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'user_profiles' 
            AND COLUMN_NAME = 'raw_profile_embedding'
        """))
        
        row = result.fetchone()
        if row and row[0] == 'NO':
            column_type = row[1].lower()
            
            if 'vector' in column_type:
                print("检测到 VECTOR 类型列，尝试删除向量索引...")
                
                try:
                    db_session.execute(text("DROP INDEX idx_raw_profile_embedding ON user_profiles"))
                    print("已删除向量索引 idx_raw_profile_embedding")
                except Exception as idx_error:
                    print(f"删除索引失败（可能已不存在）: {str(idx_error)}")
                
                print("创建新列...")
                db_session.execute(text("""
                    ALTER TABLE user_profiles 
                    ADD COLUMN raw_profile_embedding_new TEXT NULL
                """))
                
                print("删除旧 VECTOR 列...")
                db_session.execute(text("""
                    ALTER TABLE user_profiles 
                    DROP COLUMN raw_profile_embedding
                """))
                
                print("重命名新列为原始名称...")
                db_session.execute(text("""
                    ALTER TABLE user_profiles 
                    CHANGE COLUMN raw_profile_embedding_new raw_profile_embedding TEXT NULL COMMENT '用户画像语义向量（JSON格式存储）'
                """))
                
                db_session.commit()
                print("已修改 raw_profile_embedding 字段为 TEXT 类型并允许 NULL")
                print("注: 向量检索功能已禁用，如需恢复请创建新的向量索引")
            else:
                db_session.execute(text("""
                    ALTER TABLE user_profiles 
                    MODIFY COLUMN raw_profile_embedding TEXT NULL COMMENT '用户画像语义向量（JSON格式存储）'
                """))
                db_session.commit()
                print("已修改 raw_profile_embedding 字段允许 NULL")
        else:
            print("raw_profile_embedding 字段已允许 NULL，无需修改")
            
    except Exception as e:
        db_session.rollback()
        print(f"raw_profile_embedding 字段迁移失败: {str(e)}")