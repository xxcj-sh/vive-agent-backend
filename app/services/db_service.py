from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.user import User
from app.models.match import Match, MatchDetail
from app.models.match_action import MatchAction, MatchResult

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

# 匹配操作相关操作
def create_match_action(db: Session, action_data: Dict[str, Any]) -> MatchAction:
    """创建匹配操作记录"""
    try:
        db_action = MatchAction(**action_data)
        db.add(db_action)
        db.commit()
        db.refresh(db_action)
        return db_action
    except Exception as e:
        db.rollback()
        raise

def get_match_action(db: Session, action_id: str) -> Optional[MatchAction]:
    """获取匹配操作记录"""
    return db.query(MatchAction).filter(MatchAction.id == action_id).first()

def get_user_match_actions(db: Session, user_id: str, match_type: str = None, 
                          skip: int = 0, limit: int = 100) -> List[MatchAction]:
    """获取用户的匹配操作记录"""
    query = db.query(MatchAction).filter(MatchAction.user_id == user_id)
    if match_type:
        query = query.filter(MatchAction.match_type == match_type)
    return query.order_by(MatchAction.created_at.desc()).offset(skip).limit(limit).all()

def check_existing_action(db: Session, user_id: str, target_user_id: str, 
                         target_card_id: str, match_type: str) -> Optional[MatchAction]:
    """检查是否已存在匹配操作"""
    return db.query(MatchAction).filter(
        MatchAction.user_id == user_id,
        MatchAction.target_user_id == target_user_id,
        MatchAction.target_card_id == target_card_id,
        MatchAction.match_type == match_type
    ).first()

# 匹配结果相关操作
def create_match_result(db: Session, result_data: Dict[str, Any]) -> MatchResult:
    """创建匹配结果记录"""
    try:
        db_result = MatchResult(**result_data)
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return db_result
    except Exception as e:
        db.rollback()
        raise

def get_match_result(db: Session, result_id: str) -> Optional[MatchResult]:
    """获取匹配结果记录"""
    return db.query(MatchResult).filter(MatchResult.id == result_id).first()

def get_user_match_results(db: Session, user_id: str, status: str = None,
                          skip: int = 0, limit: int = 100) -> List[MatchResult]:
    """获取用户的匹配结果列表"""
    query = db.query(MatchResult).filter(
        (MatchResult.user1_id == user_id) | (MatchResult.user2_id == user_id)
    )
    if status and status != "all":
        query = query.filter(MatchResult.status == status)
    return query.order_by(MatchResult.matched_at.desc()).offset(skip).limit(limit).all()

def check_mutual_match(db: Session, user1_id: str, user2_id: str, match_type: str) -> Optional[MatchResult]:
    """检查两个用户之间是否已存在匹配结果"""
    return db.query(MatchResult).filter(
        ((MatchResult.user1_id == user1_id) & (MatchResult.user2_id == user2_id)) |
        ((MatchResult.user1_id == user2_id) & (MatchResult.user2_id == user1_id)),
        MatchResult.match_type == match_type
    ).first()

def update_match_result_activity(db: Session, result_id: str) -> Optional[MatchResult]:
    """更新匹配结果的最后活动时间"""
    from datetime import datetime
    db_result = db.query(MatchResult).filter(MatchResult.id == result_id).first()
    if db_result:
        db_result.last_activity_at = datetime.utcnow()
        db.commit()
        db.refresh(db_result)
    return db_result
