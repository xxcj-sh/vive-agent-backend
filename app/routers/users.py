from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.utils.db_config import get_db
from app.services import db_service
from app.services.data_adapter import data_service
from app.services.user_profile_service import UserProfileService
from app.dependencies import get_current_user
from app.models.user_card import (
    CardCreate, CardUpdate, Card as CardSchema,
    AllCardsResponse
)
from app.utils.db_config import get_db
from app.models.user_card import (
    CardCreate, CardUpdate, Card as CardSchema,
    AllCardsResponse
)
from app.utils.db_config import get_db

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
def update_current_user(profile_data: ProfileUpdate, current_user: Dict[str, Any] = Depends(get_current_user)):
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
        
        # 处理location字段：如果是字符串，转换为数组
        if "location" in update_dict and isinstance(update_dict["location"], str):
            location_str = update_dict["location"]
            # 按空格分割，过滤空字符串
            location_parts = [part.strip() for part in location_str.split() if part.strip()]
            update_dict["location"] = location_parts
        
        # 更新用户基础资料
        updated_user = data_service.update_profile(user_id, update_dict)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 处理图片URL，确保包含完整前缀
        processed_user = process_user_image_urls(updated_user)
        from app.models.schemas import BaseResponse
        return BaseResponse(code=0, message="success", data=processed_user)
        
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
def get_current_user_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取用户统计信息"""
    return {
        "code": 0,
        "message": "success",
        "data": {
            "matchCount": 10,
            "messageCount": 50,
            "favoriteCount": 5
        }
    }

@router.get("/me/profiles", response_model=AllCardsResponse)
def get_current_user_profiles(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有角色资料"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # 获取角色资料
    profiles_response = UserProfileService.get_user_all_profiles_response(db, user_id)
    
    # 添加用户基础资料信息
    profiles_response_dict = profiles_response.dict() if hasattr(profiles_response, 'dict') else profiles_response.__dict__
    profiles_response_dict["user_basic_info"] = current_user
    
    return profiles_response_dict

@router.get("/me/profiles/{scene_type}")
def get_current_user_profiles_by_scene(
    scene_type: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户在特定场景下的角色资料"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    profiles = UserProfileService.get_profiles_by_scene(db, user_id, scene_type)
    return {
        "code": 0,
        "message": "success",
        "data": {
            "scene_type": scene_type,
            "profiles": profiles
        }
    }

@router.get("/me/profiles/{scene_type}/{role_type}")
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
    
    profile = UserProfileService.get_user_profile_by_role(db, user_id, scene_type, role_type)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # 处理图片URL，确保包含完整前缀
    processed_profile = process_user_image_urls(profile)
    
    return {
        "code": 0,
        "message": "success",
        "data": processed_profile
    }

@router.post("/me/profiles", response_model=CardSchema)
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
    existing_profile = UserProfileService.get_user_profile_by_role(
        db, user_id, profile_data.scene_type, profile_data.role_type
    )
    if existing_profile:
        raise HTTPException(
            status_code=400, 
            detail=f"Profile for {profile_data.scene_type}.{profile_data.role_type} already exists"
        )
    
    return UserProfileService.create_profile(db, user_id, profile_data)

@router.put("/me/profiles/{profile_id}")
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
    profile = UserProfileService.get_profile_by_id(db, profile_id)
    if not profile or profile.user_id != user_id:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    updated_profile = UserProfileService.update_profile(db, profile_id, update_data)
    return {
        "code": 0,
        "message": "success",
        "data": updated_profile
    }

@router.delete("/me/profiles/{profile_id}")
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
    profile = UserProfileService.get_profile_by_id(db, profile_id)
    if not profile or profile.user_id != user_id:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    success = UserProfileService.delete_profile(db, profile_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {
        "code": 0,
        "message": "Profile deleted successfully"
    }

@router.patch("/me/profiles/{profile_id}/toggle")
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
    profile = UserProfileService.get_profile_by_id(db, profile_id)
    if not profile or profile.user_id != user_id:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    updated_profile = UserProfileService.toggle_profile_status(db, profile_id, is_active)
    return {
        "code": 0,
        "message": "Profile status updated successfully",
        "data": updated_profile
    }

@router.get("/{user_id}/profiles/{scene_type}/{role_type}")
def get_user_profile_by_role(
    user_id: str,
    scene_type: str,
    role_type: str,
    db: Session = Depends(get_db)
):
    """获取指定用户在特定场景和角色下的资料"""
    # 首先尝试作为用户ID查询
    profile = UserProfileService.get_user_profile_by_role(db, user_id, scene_type, role_type)
    
    # 如果没找到，检查user_id是否实际上是一个profile_id
    if not profile:
        # 尝试通过profile_id获取profile
        profile_by_id = UserProfileService.get_profile_by_id(db, user_id)
        if profile_by_id:
            # 获取完整的用户资料信息
            full_profile = UserProfileService.get_user_profile_by_role(
                db, str(profile_by_id.user_id), str(profile_by_id.scene_type), str(profile_by_id.role_type)
            )
            if full_profile:
                # 返回找到的profile，说明实际的类型
                return {
                    "code": 0,
                    "message": f"Found profile by ID: {profile_by_id.scene_type}.{profile_by_id.role_type}",
                    "requested": {"scene_type": scene_type, "role_type": role_type},
                    "actual": {"scene_type": profile_by_id.scene_type, "role_type": profile_by_id.role_type},
                    "data": full_profile
                }
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {
        "code": 0,
        "message": "success",
        "data": profile
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


