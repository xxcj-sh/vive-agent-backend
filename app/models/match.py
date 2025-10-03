from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.db_config import Base
import enum
import uuid

# 枚举类定义
class MatchType(str, enum.Enum):
    """匹配类型枚举"""
    DATING = "dating"           # 交友
    HOUSING = "housing"         # 房源
    ACTIVITY = "activity"       # 活动
    BUSINESS = "business"       # 商务

class MatchStatus(str, enum.Enum):
    """匹配状态枚举"""
    PENDING = "pending"         # 待处理
    ACCEPTED = "accepted"       # 已接受
    REJECTED = "rejected"       # 已拒绝
    EXPIRED = "expired"         # 已过期
    CANCELLED = "cancelled"     # 已取消

class UserRole(str, enum.Enum):
    """用户角色枚举"""
    SEEKER = "seeker"          # 寻找者
    PROVIDER = "provider"      # 提供者
    BOTH = "both"              # 双重角色

class Gender(int, enum.Enum):
    """性别枚举"""
    UNKNOWN = 0                # 未知
    MALE = 1                   # 男性
    FEMALE = 2                 # 女性

class Education(str, enum.Enum):
    """教育程度枚举"""
    HIGH_SCHOOL = "高中"        # 高中
    COLLEGE = "大专"            # 大专
    BACHELOR = "本科"           # 本科
    MASTER = "硕士"             # 硕士
    DOCTOR = "博士"             # 博士
    OTHER = "其他"              # 其他

class HousingType(str, enum.Enum):
    """房屋类型枚举"""
    WHOLE_RENT = "整租"         # 整租
    SHARED_RENT = "合租"        # 合租
    MASTER_ROOM = "主卧"        # 主卧
    SECOND_ROOM = "次卧"        # 次卧
    APARTMENT = "公寓"          # 公寓
    VILLA = "别墅"              # 别墅
    ORDINARY = "普通住宅"       # 普通住宅
    DUPLEX = "复式"             # 复式
    HOTEL_APARTMENT = "酒店式公寓"  # 酒店式公寓
    COMMERCIAL = "商住两用"     # 商住两用

class ActivityType(str, enum.Enum):
    """活动类型枚举"""
    SPORTS = "运动健身"         # 运动健身
    CULTURE = "文化艺术"        # 文化艺术
    OUTDOOR = "户外探险"        # 户外探险
    FOOD = "美食品鉴"           # 美食品鉴
    LEARNING = "学习交流"       # 学习交流
    ENTERTAINMENT = "娱乐休闲"  # 娱乐休闲
    OTHER = "其他"              # 其他

class Region(str, enum.Enum):
    """地区枚举"""
    BEIJING = "北京"
    SHANGHAI = "上海"
    GUANGZHOU = "广州"
    SHENZHEN = "深圳"
    HANGZHOU = "杭州"
    CHENGDU = "成都"
    WUHAN = "武汉"
    XIAN = "西安"
    NANJING = "南京"
    SUZHOU = "苏州"
    TIANJIN = "天津"
    CHONGQING = "重庆"
    QINGDAO = "青岛"
    DALIAN = "大连"
    XIAMEN = "厦门"
    CHANGSHA = "长沙"
    OTHER = "其他"

class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    match_type = Column(Enum(MatchType))
    status = Column(Enum(MatchStatus))
    score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="matches")
    match_details = relationship("MatchDetail", back_populates="match", cascade="all, delete-orphan")

class MatchDetail(Base):
    __tablename__ = "match_details"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String, ForeignKey("matches.id"))  # 改为String类型匹配match ID
    detail_type = Column(String)
    detail_value = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    match = relationship("Match", back_populates="match_details")
