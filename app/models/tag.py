"""
用户标签系统数据库迁移脚本
创建时间: 2025-01-28
描述: 使用 SQLAlchemy 创建 tags 和 user_tag_rel 表模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index, UniqueConstraint, and_
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import func
from app.database import Base
import enum


class TagType(str, enum.Enum):
    """标签类型枚举"""
    USER_PROFILE = "user_profile"      # 用户画像标签
    USER_SAFETY = "user_safety"        # 安全相关标签
    USER_CREDIT = "user_credit"        # 信用相关标签
    USER_COMMUNITY = "user_community"  # 社群标签（用户可创建）
    USER_FEEDBACK = "user_feedback"    # 反馈相关标签


class TagStatus(str, enum.Enum):
    """标签状态枚举"""
    ACTIVE = "ACTIVE"      # 正常
    DELETED = "DELETED"    # 已删除


class UserTagRelStatus(str, enum.Enum):
    """用户标签关联状态枚举"""
    ACTIVE = "ACTIVE"      # 正常
    DELETED = "DELETED"    # 已删除


class Tag(Base):
    """标签模型"""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(50), nullable=False, comment="标签名称")
    desc = Column(String(255), default='', comment="标签描述")
    icon = Column(String(500), default='', comment="标签图标URL")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    tag_type = Column(Enum(TagType), nullable=False, comment="标签类型")
    create_user_id = Column(String(36), nullable=False, index=True, comment="创建用户ID")
    status = Column(Enum(TagStatus), default=TagStatus.ACTIVE, comment="状态")
    max_members = Column(Integer, default=None, comment="标签最大成员数，NULL表示无限制")
    is_public = Column(Integer, default=1, comment="是否公开可见：1-是 0-否")
    member_count = Column(Integer, default=0, comment="当前成员数量")
    
    # 关系
    user_tag_rels = relationship("UserTagRel",
        back_populates="tag",
        cascade="all, delete-orphan",
        primaryjoin=lambda: (Tag.id == foreign(UserTagRel.tag_id)) & (UserTagRel.status == UserTagRelStatus.ACTIVE)
    )
    
    # 索引
    __table_args__ = (
        Index('idx_tag_type', 'tag_type'),
        Index('idx_status', 'status'),
        UniqueConstraint('name', 'tag_type', name='uk_name_type'),
    )


class UserTagRel(Base):
    """用户标签关联模型"""
    __tablename__ = "user_tag_rel"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    user_id = Column(String(36), nullable=False, index=True, comment="用户ID")
    tag_id = Column(Integer, nullable=False, index=True, comment="标签ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    status = Column(Enum(UserTagRelStatus), default=UserTagRelStatus.ACTIVE, comment="状态")
    granted_by_user_id = Column(String(36), default=None, comment="授予该标签的用户ID")
    
    # 关系
    tag = relationship("Tag", 
        back_populates="user_tag_rels",
        primaryjoin=lambda: (foreign(UserTagRel.tag_id) == Tag.id) & (Tag.status == TagStatus.ACTIVE)
    )
    
    # 索引
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_tag_id', 'tag_id'),
        Index('idx_status', 'status'),
        UniqueConstraint('user_id', 'tag_id', name='uk_user_tag'),
    )


def run_migration(db_session):
    """
    执行数据库迁移
    创建 tags 和 user_tag_rel 表
    """
    from app.database import engine
    from sqlalchemy import text
    
    try:
        # 创建表
        Base.metadata.create_all(bind=engine)
        print("标签系统表创建成功！")
        
        # 验证表是否创建成功
        result = db_session.execute(text("SHOW TABLES LIKE 'tags'"))
        if result.fetchone():
            print("tags 表已存在")
        else:
            print("tags 表创建失败")
            
        result = db_session.execute(text("SHOW TABLES LIKE 'user_tag_rel'"))
        if result.fetchone():
            print("user_tag_rel 表已存在")
        else:
            print("user_tag_rel 表创建失败")
        
        # 迁移 member_count 字段
        migrate_member_count(db_session)
            
    except Exception as e:
        print(f"数据库迁移失败: {str(e)}")
        raise


def migrate_member_count(db_session):
    """
    迁移 member_count 字段
    为所有现有标签计算并更新成员数量
    """
    from sqlalchemy import text
    
    try:
        # 检查 member_count 列是否存在
        result = db_session.execute(text("SHOW COLUMNS FROM tags LIKE 'member_count'"))
        if not result.fetchone():
            # 添加 member_count 列
            db_session.execute(text("ALTER TABLE tags ADD COLUMN member_count INT DEFAULT 0 COMMENT '当前成员数量'"))
            db_session.commit()
            print("已添加 member_count 列")
        
        # 先更新所有标签的 member_count
        db_session.execute(text("""
            UPDATE tags t
            LEFT JOIN (
                SELECT tag_id, COUNT(*) as cnt
                FROM user_tag_rel
                WHERE status = 'ACTIVE'
                GROUP BY tag_id
            ) utr ON t.id = utr.tag_id
            SET t.member_count = IFNULL(utr.cnt, 0)
        """))
        db_session.commit()
        print("member_count 迁移完成")
        
    except Exception as e:
        db_session.rollback()
        print(f"member_count 迁移失败: {str(e)}")
