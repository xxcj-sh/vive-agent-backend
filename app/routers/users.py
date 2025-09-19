from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
from app.utils.db_config import get_db
from app.services import db_service
from app.services.data_adapter import DataService
from app.services.user_card_service import UserCardService
from app.dependencies import get_current_user
from app.models.user_card import (
    CardCreate, CardUpdate, Card as CardSchema,
    AllCardsResponse
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

def ensure_full_url(url: str, base_url: str = None) -> str:
    """确保图片URL包含完整的HTTP前缀"""
    if not url:
        return url
    
    # 如果已经是完整的URL，直接返回
    if url.startswith(('http://', 'https://')):
        return url
    
    # 获取基础URL
    if not base_url:
        # 从环境变量获取，或使用默认值
        import os
        host = os.getenv('SERVER_HOST', '192.168.71.103')
        port = os.getenv('SERVER_PORT', '8000')
        base_url = f"http://{host}:{port}"
    
    # 确保URL以/开头
    if not url.startswith('/'):
        url = '/' + url
    
    return base_url + url

def process_user_image_urls(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理用户数据中的图片URL，确保包含完整前缀"""
    if not user_data:
        return user_data
    
    # 需要处理的图片字段
    image_fields = ['avatarUrl', 'avatar_url']
    
    for field in image_fields:
        if field in user_data and user_data[field]:
            user_data[field] = ensure_full_url(user_data[field])
    
    return user_data

# 用户模型
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: str = None
    email: str = None
    is_active: bool = None

class ProfileUpdate(BaseModel):
    # 支持驼峰命名
    nickName: Optional[str] = None
    avatarUrl: Optional[str] = None
    matchType: Optional[str] = None
    userRole: Optional[str] = None
    
    # 支持下划线命名（前端可能使用的格式）
    nick_name: Optional[str] = None
    avatar_url: Optional[str] = None
    match_type: Optional[str] = None
    user_role: Optional[str] = None
    
    # 其他字段
    gender: Optional[int] = None
    age: Optional[int] = None
    occupation: Optional[str] = None
    location: Optional[Any] = None  # 支持字符串或数组格式
    bio: Optional[str] = None
    interests: Optional[List[str]] = None  # 明确指定为字符串列表
    preferences: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    wechat: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    level: Optional[int] = None
    points: Optional[int] = None
    lastLogin: Optional[datetime] = None
    
    class Config:
        # 允许额外字段，提高兼容性
        extra = "ignore"
        # 允许任意类型
        arbitrary_types_allowed = True

class User(UserBase):
    id: str
    is_active: bool

    class Config:
        orm_mode = True

# 路由
@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 在实际应用中，这里应该对密码进行哈希处理
    hashed_password = user.password  # 简化示例，实际应使用哈希
    
    user_data = user.dict()
    user_data.pop("password")
    user_data["hashed_password"] = hashed_password
    
    return db_service.create_user(db=db, user_data=user_data)

@router.get("/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db_service.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/me")
def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前用户基础信息"""
    from app.models.schemas import BaseResponse
    
    # 创建DataService实例
    data_service = DataService()
    
    # 从数据服务获取最新的用户数据，而不是使用缓存的认证数据
    user_id = current_user.get("id")
    if user_id:
        # 重新从数据服务获取最新用户数据
        latest_user_data = data_service.get_user_by_id(user_id)
        if latest_user_data:
            # 处理图片URL，确保包含完整前缀
            processed_data = process_user_image_urls(latest_user_data)
            # 添加createdAt字段
            if 'created_at' in processed_data:
                processed_data['createdAt'] = processed_data['created_at']
            return BaseResponse(code=0, message="success", data=processed_data)
    
    # 如果获取失败，返回认证数据作为备选
    processed_data = process_user_image_urls(current_user)
    return BaseResponse(code=0, message="success", data=processed_data)

@router.put("/me")
def update_current_user(profile_data: ProfileUpdate, current_user: Dict[str, Any] = Depends(get_current_user), db: Session = Depends(get_db)):
    """更新当前用户基础信息"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # 转换为字典，排除未设置的字段
    update_dict = profile_data.dict(exclude_unset=True)
    # 验证更新数据不为空
    if not update_dict:
        raise HTTPException(status_code=422, detail="No valid fields provided for update")
    
    # 数据预处理
    try:
        # 字段名统一处理：将下划线命名转换为驼峰命名
        field_mapping = {
            'nick_name': 'nickName',
            'avatar_url': 'avatarUrl', 
            'match_type': 'matchType',
            'user_role': 'userRole'
        }
        
        # 应用字段映射
        for old_field, new_field in field_mapping.items():
            if old_field in update_dict:
                # 如果同时存在两种命名，优先使用下划线命名的值
                update_dict[new_field] = update_dict.pop(old_field)
        
        # 处理location字段：支持字符串和数组格式
        if "location" in update_dict:
            if isinstance(update_dict["location"], str):
                location_str = update_dict["location"]
                # 按空格分割，过滤空字符串
                location_parts = [part.strip() for part in location_str.split() if part.strip()]
                update_dict["location"] = location_parts
            elif isinstance(update_dict["location"], list):
                # 如果已经是数组格式，确保数组元素都是字符串且过滤空值
                location_parts = [str(part).strip() for part in update_dict["location"] if part and str(part).strip()]
                update_dict["location"] = location_parts
            else:
                # 其他格式转换为空数组
                update_dict["location"] = []
        print("user_id", user_id, "update_dict", update_dict)
        # 更新用户基础资料
        updated_user = db_service.update_user(db, user_id, update_dict)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        from app.models.schemas import BaseResponse
        # 移除SQLAlchemy内部字段并返回干净的用户数据
        user_dict = updated_user.__dict__.copy()
        user_dict.pop('_sa_instance_state', None)
        return BaseResponse(code=0, message="用户信息更新成功", data=process_user_image_urls(user_dict))
        
    except Exception as e:
        print(f"更新用户信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新用户信息失败: {str(e)}")

@router.delete("/me")
def delete_current_user(current_user: Dict[str, Any] = Depends(get_current_user), db: Session = Depends(get_db)):
    """注销当前用户账户（软删除）"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    try:
        # 获取用户信息
        user = db_service.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 检查用户是否已经被删除
        if user.status == "deleted":
            raise HTTPException(status_code=400, detail="User account already deleted")
        
        # 执行软删除操作
        delete_data = {
            "status": "deleted",  # 状态改为已删除
            "nick_name": f"已注销用户_{user_id[:8]}",  # 匿名化昵称
            "avatar_url": "",  # 清空头像
            "phone": None,  # 清空手机号
            "email": None,  # 清空邮箱
            "wechat": None,  # 清空微信号
            "bio": None,  # 清空个人简介
            "occupation": None,  # 清空职业信息
            "education": None,  # 清空教育信息
            "location": None,  # 清空位置信息
            "interests": None,  # 清空兴趣爱好
            "is_active": False  # 设置为非活跃状态
        }
        
        # 更新用户信息
        updated_user = db_service.update_user(db, user_id, delete_data)
        if not updated_user:
            raise HTTPException(status_code=500, detail="Failed to delete user account")
        
        from app.models.schemas import BaseResponse
        return BaseResponse(code=0, message="账户注销成功", data={"userId": user_id})
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"注销用户账户失败: {e}")
        raise HTTPException(status_code=500, detail=f"注销用户账户失败: {str(e)}")
        
    except ValueError as ve:
        print(f"ERROR: Validation error: {str(ve)}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(ve)}")
    except Exception as e:
        print(f"ERROR: Failed to update user profile: {str(e)}")
        print(f"ERROR: Exception type: {type(e).__name__}")
        import traceback
        print(f"ERROR: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=422, detail=f"Failed to update profile: {str(e)}")

@router.get("/me/stats")
def get_current_user_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户真实统计信息"""
    try:
        from app.services.user_stats_service import UserStatsService
        
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        stats_service = UserStatsService(db)
        stats = stats_service.get_user_stats(user_id)
        
        return {
            "code": 0,
            "message": "success",
            "data": stats
        }
        
    except Exception as e:
        print(f"获取用户统计失败: {str(e)}")
        return {
            "code": 500,
            "message": f"获取统计信息失败: {str(e)}",
            "data": {
                "matchCount": 0,
                "messageCount": 0,
                "favoriteCount": 0,
                "newMatches": 0,
                "unreadMessages": 0,
                "activeMatches": 0
            }
        }

@router.get("/me/cards", response_model=AllCardsResponse)
def get_current_user_cards(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有角色资料"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # 获取角色资料
    cards_response = UserCardService.get_user_all_cards_response(db, user_id)
    
    # 添加用户基础资料信息
    cards_response_dict = cards_response.model_dump() if hasattr(cards_response, 'model_dump') else cards_response.dict()
    cards_response_dict["user_basic_info"] = current_user
    
    return cards_response_dict

@router.get("/me")
def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的完整信息"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    db_user = db_service.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": db_user.id,
            "nickName": db_user.nick_name,
            "avatarUrl": db_user.avatar_url,
            "gender": db_user.gender or 0,
            "age": db_user.age,
            "occupation": db_user.occupation,
            "location": db_user.location,
            "education": db_user.education,
            "interests": db_user.interests,
            "wechat": db_user.wechat,
            "email": db_user.email,
            "status": db_user.status,
            "level": db_user.level,
            "points": db_user.points,
            "lastLogin": db_user.last_login.isoformat() if db_user.last_login else None,
            "registerAt": db_user.register_at.isoformat() if db_user.register_at else None,
            "phone": db_user.phone,
            "createdAt": db_user.created_at.isoformat() if db_user.created_at else None,
            "updatedAt": db_user.updated_at.isoformat() if db_user.updated_at else None
        }
    }

@router.get("/me/cards/{scene_type}")
def get_current_user_cards_by_scene(
    scene_type: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户在特定场景下的角色资料"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    cards = UserCardService.get_cards_by_scene(db, user_id, scene_type)
    return {
        "code": 0,
        "message": "success",
        "data": {
            "scene_type": scene_type,
            "cards": cards
        }
    }

@router.get("/me/cards/{scene_type}/{role_type}")
def get_current_user_profile_by_role(
    scene_type: str,
    role_type: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户在特定场景和角色下的资料"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    card = UserCardService.get_user_card_by_role(db, user_id, scene_type, role_type)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # 处理图片URL，确保包含完整前缀
    processed_card = process_user_image_urls(card)
    
    return {
        "code": 0,
        "message": "success",
        "data": processed_card
    }

@router.post("/me/cards", response_model=CardSchema)
def create_user_profile(
    profile_data: CardCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建用户角色资料"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # 检查是否已存在相同场景和角色的资料
    existing_card = UserCardService.get_user_card_by_role(
        db, user_id, profile_data.scene_type, profile_data.role_type
    )
    if existing_card:
        raise HTTPException(
            status_code=400, 
            detail=f"Card for {profile_data.scene_type}.{profile_data.role_type} already exists"
        )
    
    return UserCardService.create_card(db, user_id, profile_data)

@router.put("/me/cards/{profile_id}")
def update_user_profile(
    profile_id: str,
    update_data: CardUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户角色资料"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # 验证资料属于当前用户
    card = UserCardService.get_card_by_id(db, profile_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # 将Pydantic模型转换为字典
    update_dict = update_data.dict(exclude_unset=True)
    updated_card = UserCardService.update_card(db, profile_id, update_dict)
    return {
        "code": 0,
        "message": "success",
        "data": updated_card
    }

@router.delete("/me/cards/{profile_id}")
def delete_user_profile(
    profile_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户角色资料"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # 验证资料属于当前用户
    card = UserCardService.get_card_by_id(db, profile_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    
    success = UserCardService.delete_card(db, profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return {
        "code": 0,
        "message": "Card deleted successfully"
    }

@router.patch("/me/cards/{profile_id}/toggle")
def toggle_user_profile_status(
    profile_id: str,
    is_active: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换用户角色资料的激活状态"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # 验证资料属于当前用户
    card = UserCardService.get_card_by_id(db, profile_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    
    updated_card = UserCardService.toggle_card_status(db, profile_id, is_active)
    return {
        "code": 0,
        "message": "Card status updated successfully",
        "data": updated_card
    }

@router.get("/{user_id}/cards/{scene_type}/{role_type}")
def get_user_profile_by_role(
    user_id: str,
    scene_type: str,
    role_type: str,
    db: Session = Depends(get_db)
):
    """获取指定用户在特定场景和角色下的资料"""
    # 首先尝试作为用户ID查询
    card = UserCardService.get_user_card_by_role(db, user_id, scene_type, role_type)
    
    # 如果没找到，检查user_id是否实际上是一个card_id
    if not card:
        # 尝试通过card_id获取card
        card_by_id = UserCardService.get_card_by_id(db, user_id)
        if card_by_id:
            # 获取完整的用户资料信息
            full_card = UserCardService.get_user_card_by_role(
                db, str(card_by_id.user_id), str(card_by_id.scene_type), str(card_by_id.role_type)
            )
            if full_card:
                # 返回找到的card，说明实际的类型
                return {
                    "code": 0,
                    "message": f"Found card by ID: {card_by_id.scene_type}.{card_by_id.role_type}",
                    "requested": {"scene_type": scene_type, "role_type": role_type},
                    "actual": {"scene_type": card_by_id.scene_type, "role_type": card_by_id.role_type},
                    "data": full_card
                }
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return {
        "code": 0,
        "message": "success",
        "data": card
    }

@router.get("/{user_id}")
def read_user(user_id: str, db: Session = Depends(get_db)):
    from app.models.schemas import BaseResponse
    db_user = db_service.get_user(db, user_id=user_id)
    if db_user is None:
        return BaseResponse(code=404, message="User not found", data={})
    
    return BaseResponse(
        code=0,
        message="success",
        data={
            "id": db_user.id,
            "nickname": db_user.nick_name,
            "avatarUrl": db_user.avatar_url,
            "gender": db_user.gender or 0,
            "age": db_user.age,
            "occupation": db_user.occupation,
            "location": db_user.location,
            "education": db_user.education,
            "interests": db_user.interests,
            "wechat": db_user.wechat,
            "email": db_user.email,
            "status": db_user.status,
            "level": db_user.level,
            "points": db_user.points,
            "lastLogin": db_user.last_login.isoformat() if db_user.last_login else None,
            "phone": getattr(db_user, 'phone', None)
        }
    )

@router.put("/{user_id}", response_model=User)
def update_user(user_id: str, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db_service.update_user(db, user_id=user_id, user_data=user.dict(exclude_unset=True))
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    success = db_service.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted"}


