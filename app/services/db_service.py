from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.user import User
from app.models.match import Match, MatchDetail

# 用户相关操作
def create_user(db: Session, user_data: Dict[str, Any]) -> User:
    """创建用户"""
    try:
        # 如果没有提供ID，生成一个UUID
        if 'id' not in user_data:
            import uuid
            user_data['id'] = str(uuid.uuid4())
        
        db_user = User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise

def get_user(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
    """根据手机号获取用户"""
    return db.query(User).filter(User.phone == phone).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: str, user_data: Dict[str, Any]) -> Optional[User]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        # 字段映射：前端字段名 -> 数据库字段名
        field_mapping = {
            'nickName': 'nick_name',
            'avatarUrl': 'avatar_url',
            'matchType': 'match_type',
            'userRole': 'user_role',
            'joinDate': 'join_date'
        }
        
        for key, value in user_data.items():
            # 使用映射后的字段名，如果没有映射则使用原字段名
            db_field = field_mapping.get(key, key)
            if hasattr(db_user, db_field):
                setattr(db_user, db_field, value)
        
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: str) -> bool:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

# 匹配相关操作
def create_match(db: Session, match_data: Dict[str, Any], details: List[Dict[str, Any]] = None) -> Match:
    db_match = Match(**match_data)
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    
    # 添加匹配详情
    if details:
        for detail in details:
            detail["match_id"] = db_match.id
            db_detail = MatchDetail(**detail)
            db.add(db_detail)
        db.commit()
    
    return db_match

def get_match(db: Session, match_id: str) -> Optional[Match]:
    return db.query(Match).filter(Match.id == match_id).first()

def get_matches(db: Session, user_id: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Match]:
    query = db.query(Match)
    if user_id:
        query = query.filter(Match.user_id == user_id)
    return query.offset(skip).limit(limit).all()

def update_match(db: Session, match_id: str, match_data: Dict[str, Any]) -> Optional[Match]:
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if db_match:
        for key, value in match_data.items():
            setattr(db_match, key, value)
        db.commit()
        db.refresh(db_match)
    return db_match

def delete_match(db: Session, match_id: str) -> bool:
    db_match = db.query(Match).filter(Match.id == match_id).first()
    if db_match:
        # 删除相关的匹配详情
        db.query(MatchDetail).filter(MatchDetail.match_id == match_id).delete()
        db.delete(db_match)
        db.commit()
        return True
    return False

# 匹配详情相关操作
def add_match_detail(db: Session, match_id: str, detail_data: Dict[str, Any]) -> MatchDetail:
    detail_data["match_id"] = match_id
    db_detail = MatchDetail(**detail_data)
    db.add(db_detail)
    db.commit()
    db.refresh(db_detail)
    return db_detail

def get_match_details(db: Session, match_id: str) -> List[MatchDetail]:
    return db.query(MatchDetail).filter(MatchDetail.match_id == match_id).all()
