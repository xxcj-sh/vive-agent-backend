from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
from enum import Enum
import httpx
import os
from app.utils.db_config import get_db
from app.models.user import User
from sqlalchemy import func
from app.services.data_adapter import DataService
from app.services.user_card_service import UserCardService
from app.dependencies import get_current_user
from app.models.schemas import BaseResponse
from app.models.user_card import (
    CardCreate, CardUpdate, Card as CardSchema,
    AllCardsResponse
)
from app.models.user_card import CardCreate
from app.models.enums import SceneType, UserRoleType
from app.services.embedding_service import embedding_service
from app.services.user_profile.user_profile_service import UserProfileService
from app.services.llm_service import LLMService
from app.models.llm_schemas import LLMProvider, LLMRequest

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
    username: Optional[str] = None
    email: Optional[str] = None

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
    location: Optional[Any] = None
    bio: Optional[str] = None
    birthday: Optional[str] = None
    interests: Optional[List[str]] = None
    preferences: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    wechat: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    level: Optional[int] = None
    points: Optional[int] = None
    lastLogin: Optional[datetime] = None
    
    # 社交媒体账号
    xiaohongshuId: Optional[str] = None
    douyinId: Optional[str] = None
    wechatOfficialAccount: Optional[str] = None
    xiaoyuzhouId: Optional[str] = None
    
    # 下划线命名
    xiaohongshu_id: Optional[str] = None
    douyin_id: Optional[str] = None
    wechat_official_account: Optional[str] = None
    xiaoyuzhou_id: Optional[str] = None
    
    class Config:
        # 允许额外字段，提高兼容性
        extra = "ignore"
        # 允许任意类型
        arbitrary_types_allowed = True

class UserResponse(BaseModel):
    id: str
    is_active: bool
    email: Optional[str] = None
    phone: Optional[str] = None
    nick_name: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[Any] = None
    education: Optional[str] = None
    interests: Optional[List[str]] = None
    wechat: Optional[str] = None
    status: Optional[str] = None
    level: Optional[int] = None
    points: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class WeChatCodeRequest(BaseModel):
    """微信小程序 code 换取 openid 请求模型"""
    code: str = Field(..., description="微信登录凭证 code")
    user_id: Optional[str] = Field(None, description="用户ID，可选")


class WeChatOpenIdResponse(BaseModel):
    """微信 openid 响应模型"""
    openid: str = Field(..., description="微信用户唯一标识")
    session_key: Optional[str] = Field(None, description="会话密钥")
    unionid: Optional[str] = Field(None, description="用户在开放平台的唯一标识符")
    user_id: Optional[str] = Field(None, description="用户ID")


def trigger_user_profile_generation(db: Session, user_id: str, user_data: Dict[str, Any]):
    """
    后台任务：触发用户画像生成
    
    这个函数作为 BackgroundTasks 传入，确保在请求返回后继续执行
    """
    from app.services.user_profile.user_profile_service import UserProfileService
    import asyncio
    
    async def _generate():
        try:
            profile_service = UserProfileService(db)
            await profile_service.refresh_profile_on_user_update(user_id, user_data)
            print(f"用户画像生成完成: user_id={user_id}")
        except Exception as e:
            print(f"用户画像生成失败: user_id={user_id}, error={str(e)}")
    
    # 创建新的事件循环来执行异步任务
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate())
        loop.close()
    except Exception as e:
        print(f"执行用户画像生成任务失败: user_id={user_id}, error={str(e)}")


def generate_profile_on_user_creation(db: Session, user_id: str):
    """
    用户创建时生成初始画像
    """
    from app.services.user_profile.user_profile_service import UserProfileService
    import asyncio
    
    async def _generate():
        try:
            profile_service = UserProfileService(db)
            
            # 获取用户信息
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"用户不存在，无法生成画像: user_id={user_id}")
                return
            
            user_data = {
                'nick_name': user.nick_name,
                'gender': user.gender,
                'age': user.age,
                'bio': user.bio,
                'occupation': user.occupation,
                'location': user.location,
                'education': user.education,
                'interests': user.interests
            }
            
            await profile_service.generate_profile_from_user_data(
                user_id=user_id,
                user_data=user_data,
                existing_profile=None
            )
            print(f"用户创建时画像生成完成: user_id={user_id}")
        except Exception as e:
            print(f"用户创建时画像生成失败: user_id={user_id}, error={str(e)}")
    
    # 创建新的事件循环来执行异步任务
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate())
        loop.close()
    except Exception as e:
        print(f"执行用户创建画像生成任务失败: user_id={user_id}, error={str(e)}")



# 路由
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 在实际应用中，这里应该对密码进行哈希处理
    hashed_password = user.password  # 简化示例，实际应使用哈希
    
    user_data = user.dict()
    user_data.pop("password")
    user_data["hashed_password"] = hashed_password
    user_data["points"] = 0
    
    # 创建用户
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    new_user = db_user
    
    # 用户注册成功后，自动创建一张 SOCIAL_BASIC 身份卡片
    try:
        # 构建 SOCIAL_BASIC 卡片数据
        social_basic_card = CardCreate(
            role_type=UserRoleType.SOCIAL_BASIC.value,
            display_name=new_user.nick_name or f"用户{new_user.id[:8]}",
            avatar_url=new_user.avatar_url or "https://picsum.photos/200/200?random=default",
            bio=new_user.bio or "",
            visibility="public"
        )
        
        # 创建卡片
        UserCardService.create_card(db, new_user.id, social_basic_card)
        print(f"自动创建 SOCIAL_BASIC 卡片成功，用户ID: {new_user.id}")
        
    except Exception as e:
        # 如果卡片创建失败，只记录日志，不影响用户注册流程
        print(f"自动创建 SOCIAL_BASIC 卡片失败，用户ID: {new_user.id}, 错误: {str(e)}")
    
    # 用户注册成功后，异步生成用户画像
    background_tasks.add_task(generate_profile_on_user_creation, db, new_user.id)
    
    return BaseResponse(
        code=0, 
        message="用户创建成功", 
        data=UserResponse.from_orm(new_user).dict()
    )

@router.get("/", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/me")
def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前用户基础信息"""
    from app.models.schemas import BaseResponse
    
    # 检查用户是否已认证
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
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
def update_current_user(profile_data: ProfileUpdate, background_tasks: BackgroundTasks, current_user: Dict[str, Any] = Depends(get_current_user), db: Session = Depends(get_db)):
    """更新当前用户基础信息"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
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
        # 字段名统一处理：将驼峰命名转换为下划线命名
        # 优先使用下划线命名的值，如果下划线版本已存在则保留
        field_mapping = {
            'nickName': 'nick_name',
            'avatarUrl': 'avatar_url',
            'matchType': 'match_type',
            'userRole': 'user_role',
            'xiaohongshuId': 'xiaohongshu_id',
            'douyinId': 'douyin_id',
            'wechatOfficialAccount': 'wechat_official_account',
            'xiaoyuzhouId': 'xiaoyuzhou_id'
        }
        
        # 应用字段映射：驼峰 -> 下划线
        for camel_field, snake_field in field_mapping.items():
            if camel_field in update_dict:
                # 如果下划线版本不存在，才使用驼峰版本的值
                if snake_field not in update_dict:
                    update_dict[snake_field] = update_dict.pop(camel_field)
                else:
                    # 下划线版本已存在，移除驼峰版本
                    update_dict.pop(camel_field, None)
        
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
        # 更新用户基础资料
        try:
            db_user = db.query(User).filter(User.id == user_id).first()
        except Exception as query_error:
            print(f"查询用户时出错: {query_error}")
            print(f"错误类型: {type(query_error)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"查询用户失败: {str(query_error)}")
            
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            for key, value in update_dict.items():
                setattr(db_user, key, value)
            db.commit()
            db.refresh(db_user)
            updated_user = db_user
        except Exception as update_error:
            import traceback
            traceback.print_exc()
            db.rollback()
            raise HTTPException(status_code=500, detail=f"更新用户失败: {str(update_error)}")
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 检查是否需要触发用户画像生成
        # 当用户更新了关键信息（bio, gender, age, occupation, location）时重新生成画像
        profile_trigger_fields = ['bio', 'gender', 'age', 'occupation', 'location', 'nick_name', 'education', 'interests']
        should_regenerate_profile = any(
            field in update_dict for field in profile_trigger_fields
        )
        
        if should_regenerate_profile:
            # 准备用户数据
            user_data_for_profile = {
                'nick_name': updated_user.nick_name,
                'gender': updated_user.gender,
                'age': updated_user.age,
                'bio': updated_user.bio,
                'occupation': updated_user.occupation,
                'location': updated_user.location,
                'education': updated_user.education,
                'interests': updated_user.interests
            }
            
            # 使用 BackgroundTasks 异步触发画像生成（不阻塞响应）
            background_tasks.add_task(trigger_user_profile_generation, db, user_id, user_data_for_profile)
            print(f"用户信息更新后已触发画像生成，用户ID: {user_id}")
        
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
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    try:
        # 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
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
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=500, detail="Failed to delete user account")
        for key, value in delete_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
        updated_user = db_user
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
    """获取用户真实统计信息，包括积分和等级"""
    try:
        from app.models.user import User
        from sqlalchemy.orm import Session
        
        if not current_user:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # 查询用户基本信息（包括积分和等级）
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 返回包含积分和等级的用户信息
        return {
            "code": 0,
            "message": "success",
            "data": {
                "userId": user_id,
                "nickName": user.nick_name,
                "avatarUrl": user.avatar_url,
                "level": user.level,
                "points": user.points,
                "status": user.status,
                "createdAt": user.created_at.isoformat() if user.created_at else None,
                "lastLogin": user.last_login.isoformat() if user.last_login else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取用户统计失败: {str(e)}")
        return {
            "code": 500,
            "message": f"获取统计信息失败: {str(e)}",
            "data": {
                "userId": "",
                "nickName": "",
                "avatarUrl": "",
                "level": 1,
                "points": 0,
                "status": "pending",
                "createdAt": None,
                "lastLogin": None
            }
        }

@router.get("/me/cards", response_model=AllCardsResponse)
def get_current_user_cards(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有角色资料"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
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
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    db_user = db.query(User).filter(User.id == user_id).first()
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

@router.get("/me/cards")
def get_user_cards_by_scene(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有角色资料"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    cards = UserCardService.get_cards_by_scene(db, user_id)
    return {
        "code": 0,
        "message": "success",
        "data": {
            "cards": cards
        }
    }

@router.get("/me/cards/{role_type}")
def get_current_user_profile_by_role(
    role_type: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户在特定角色下的资料"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    card = UserCardService.get_user_card_by_role(db, user_id, role_type)
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
    
    # 检查是否已存在相同角色的资料
    existing_card = UserCardService.get_user_card_by_role(
        db, user_id, profile_data.role_type
    )
    if existing_card:
        raise HTTPException(
            status_code=400, 
            detail=f"Card for {profile_data.role_type} already exists"
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

@router.get("/{user_id}/cards/{role_type}")
def get_user_profile_by_role(
    user_id: str,
    role_type: str,
    db: Session = Depends(get_db)
):
    """获取指定用户在特定角色下的资料"""
    # 首先尝试作为用户ID查询
    card = UserCardService.get_user_card_by_role(db, user_id, role_type)
    
    # 如果没找到，检查user_id是否实际上是一个card_id
    if not card:
        # 尝试通过card_id获取card
        card_by_id = UserCardService.get_card_by_id(db, user_id)
        if card_by_id:
            # 获取完整的用户资料信息
            full_card = UserCardService.get_user_card_by_role(
                db, str(card_by_id.user_id), str(card_by_id.role_type)
            )
            if full_card:
                # 返回找到的card，说明实际的类型
                return {
                    "code": 0,
                    "message": f"Found card by ID: {card_by_id.role_type}",
                    "requested": {"role_type": role_type},
                    "actual": {"role_type": card_by_id.role_type},
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
    db_user = db.query(User).filter(User.id == user_id).first()
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
            "wechat_open_id": db_user.wechat_open_id,
            "email": db_user.email,
            "status": db_user.status,
            "level": db_user.level,
            "points": db_user.points,
            "lastLogin": db_user.last_login.isoformat() if db_user.last_login else None,
            "phone": getattr(db_user, 'phone', None)
        }
    )

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, user: ProfileUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user.dict(exclude_unset=True)
    
    # 处理字段名映射（驼峰命名到蛇形命名）
    field_mapping = {
        'nickName': 'nick_name',
        'avatarUrl': 'avatar_url',
        'matchType': 'match_type',
        'userRole': 'user_role',
        'lastLogin': 'last_login'
    }
    
    # 转换字段名
    converted_data = {}
    for key, value in update_data.items():
        if key in field_mapping:
            converted_data[field_mapping[key]] = value
        else:
            converted_data[key] = value
    
    # 应用更新
    for key, value in converted_data.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    success = db_service.delete_user(db, user_id=user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted"}


@router.post("/wechat/openid", response_model=BaseResponse)
async def get_wechat_openid(request: WeChatCodeRequest, db: Session = Depends(get_db)):
    """
    微信小程序 code 换取 openid
    
    参考微信官方文档：https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-login/code2Session.html
    """
    try:
        # 获取微信配置
        app_id = os.getenv("WECHAT_APP_ID")
        app_secret = os.getenv("WECHAT_APP_SECRET")
        
        if not app_id or not app_secret:
            raise HTTPException(
                status_code=500, 
                detail="微信配置缺失，请联系管理员配置 WECHAT_APP_ID 和 WECHAT_APP_SECRET"
            )
        
        # 调用微信 code2Session 接口
        async with httpx.AsyncClient() as client:
            url = "https://api.weixin.qq.com/sns/jscode2session"
            params = {
                "appid": app_id,
                "secret": app_secret,
                "js_code": request.code,
                "grant_type": "authorization_code"
            }
            
            response = await client.get(url, params=params)
            result = response.json()
            print("微信接口返回:", result)
            # 检查微信接口返回的错误
            if "errcode" in result and result["errcode"] != 0:
                error_msg = result.get("errmsg", "未知错误")
                raise HTTPException(
                    status_code=400, 
                    detail=f"微信接口错误: {error_msg} (错误码: {result['errcode']})"
                )
            
            # 检查必要的返回字段
            if "openid" not in result:
                raise HTTPException(
                    status_code=400, 
                    detail="微信接口未返回 openid"
                )
            
            openid = result["openid"]
            session_key = result.get("session_key")
            unionid = result.get("unionid")
            
            # 如果提供了 user_id，更新用户的微信 openid
            if request.user_id:
                db_user = db.query(User).filter(User.id == request.user_id).first()
                if db_user:
                    db_user.wechat_open_id = openid
                    db.commit()
                    print(f"已更新用户 {request.user_id} 的微信 openid: {openid}")
            
            return BaseResponse(
                code=0,
                message="success",
                data={
                    "openid": openid,
                    "session_key": session_key,
                    "unionid": unionid,
                    "user_id": request.user_id
                }
            )
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, 
            detail=f"微信接口请求失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"获取微信 openid 失败: {str(e)}"
        )

@router.get("/{user_id}/cards")
def get_user_card_by_user_id(
    user_id: str,
    db: Session = Depends(get_db)
):
    """根据用户ID获取该用户创建的user cards
    
    这是一个公开接口，不需要用户认证，用于获取指定用户的卡片信息
    """
    try:
        # 获取用户的所有卡片
        cards_response = UserCardService.get_user_all_cards_response(db, user_id)
        if not cards_response or not cards_response.all_cards:
            return {
                "code": 0,
                "message": "该用户暂无卡片",
                "data": {
                    "cards": [],
                    "total": 0,
                    "user_id": user_id
                }
            }
        
        # 处理图片URL，确保包含完整前缀
        processed_cards = []
        for card in cards_response.all_cards:
            processed_card = process_user_image_urls(card)
            processed_cards.append(processed_card)
        
        return {
            "code": 0,
            "message": "success",
            "data": {
                "cards": processed_cards,
                "total": len(processed_cards),
                "user_id": user_id
            }
        }
        
    except Exception as e:
        print(f"获取用户卡片失败: {str(e)}")
        return {
            "code": 500,
            "message": f"获取用户卡片失败: {str(e)}",
            "data": {
                "cards": [],
                "total": 0,
                "user_id": user_id
            }
        }


class SemanticSearchRequest(BaseModel):
    """语义搜索请求模型"""
    query: str = Field(..., description="用户的自然语言搜索查询", min_length=1, max_length=500)
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=100)


class SemanticSearchItem(BaseModel):
    """搜索结果项模型"""
    user_id: str = Field(..., description="用户ID")
    name: Optional[str] = Field(None, description="用户名称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    gender: Optional[int] = Field(None, description="性别：1-男，2-女")
    age: Optional[int] = Field(None, description="年龄")
    location: Optional[Any] = Field(None, description="位置信息")
    occupation: Optional[str] = Field(None, description="职业")
    interests: Optional[List[str]] = Field(None, description="兴趣爱好")
    similarity: float = Field(..., description="相似度分数")


class SemanticSearchResponse(BaseModel):
    """语义搜索响应模型"""
    items: List[SemanticSearchItem] = Field(default_factory=list, description="搜索结果列表")
    expanded_queries: List[str] = Field(default_factory=list, description="LLM扩展的搜索语句")
    display_reasons: Dict[str, str] = Field(default_factory=dict, description="每个用户的AI展示理由")
    total: int = Field(0, description="总结果数")


async def expand_query_with_llm(query: str, llm_service: LLMService) -> List[str]:
    """
    使用 LLM 对用户查询进行语义改写和扩展，生成多条近似搜索语句

    Args:
        query: 用户的原始搜索查询
        llm_service: LLM服务实例

    Returns:
        扩展后的搜索语句列表
    """
    prompt = f"""
用户想要搜索符合以下条件的人：

"{query}"

请根据这个搜索条件，生成 3 条语义相近但表述不同的搜索语句。每条语句应该：
1. 保持原始搜索意图
2. 使用不同的表达方式
3. 覆盖更多可能的同义词和描述方式

请直接返回 3 条搜索语句，每条一行，不要添加任何解释或编号。
"""

    try:
        request = LLMRequest(
            user_id="system",
            prompt=prompt,
            task_type="semantic_search_expansion"
        )

        response = await llm_service.call_llm_api(
            request=request,
            provider=LLMProvider.VOLCENGINE
        )

        if response.success and response.data:
            # 解析LLM返回的查询扩展结果
            expanded_queries = []
            for line in response.data.strip().split('\n'):
                line = line.strip()
                # 过滤掉空行和可能的编号
                if line and not line.startswith('#'):
                    # 移除可能的编号前缀如 "1. " 或 "① "
                    cleaned_line = line
                    for prefix in ['1. ', '2. ', '3. ', '① ', '② ', '③ ', '- ', '* ']:
                        if cleaned_line.startswith(prefix):
                            cleaned_line = cleaned_line[len(prefix):]
                    if cleaned_line:
                        expanded_queries.append(cleaned_line)

            # 确保返回恰好3条
            while len(expanded_queries) < 3:
                expanded_queries.append(query)

            return expanded_queries[:3]

    except Exception as e:
        print(f"[SemanticSearch] LLM查询扩展失败: {str(e)}")

    # 如果LLM调用失败，返回原始查询作为默认
    return [query, query, query]


async def generate_display_reasons(
    query: str,
    candidates: List[Dict[str, Any]],
    llm_service: LLMService
) -> Dict[str, str]:
    """
    使用 LLM 为每个候选用户生成展示理由

    Args:
        query: 用户的搜索查询
        candidates: 候选用户列表
        llm_service: LLM服务实例

    Returns:
        user_id -> 展示理由 的映射字典
    """
    if not candidates:
        return {}

    # 构建提示信息
    candidate_info = []
    for i, candidate in enumerate(candidates[:10]):  # 最多处理10个候选用户
        raw_profile = candidate.get('raw_profile', {})
        user_id = candidate["user_id"]
        if isinstance(raw_profile, dict):
            name = raw_profile.get('nickname', raw_profile.get('name', f'用户{candidate["user_id"][:8]}'))
            bio = raw_profile.get('bio', raw_profile.get('description', ''))
        else:
            name = f'用户{candidate["user_id"][:8]}'
            bio = str(raw_profile)[:200] if raw_profile else ''

        candidate_info.append(f"{i+1}. 用户ID {user_id}, 用户名：{name}, 个人简介：{bio}")

    candidates_text = '\n'.join(candidate_info)

    prompt = f"""
用户想要搜索："{query}"

以下是搜索到的候选用户信息：

{candidates_text}

请为每个用户生成一个简短的展示理由，说明为什么这个用户符合搜索条件。
理由应该：
1. 突出用户与搜索条件的匹配点
2. 语言简洁自然，不超过30个字
3. 包含具体的关键信息

请按编号顺序返回JSON格式的理由列表，格式如下：
{{
    "user_1_id": "理由1",
    "user_2_id": "理由2",
    ...
}}
"""

    try:
        request = LLMRequest(
            user_id="system",
            prompt=prompt,
            task_type="display_reason_generation"
        )

        response = await llm_service.call_llm_api(
            request=request,
            provider=LLMProvider.VOLCENGINE
        )

        if response.success and response.data:
            # 尝试解析JSON响应
            try:
                # 尝试直接解析
                reasons = json.loads(response.data)
                if isinstance(reasons, dict):
                    return reasons
            except json.JSONDecodeError:
                pass

            # 如果直接解析失败，尝试提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response.data)
            if json_match:
                try:
                    reasons = json.loads(json_match.group())
                    if isinstance(reasons, dict):
                        return reasons
                except json.JSONDecodeError:
                    pass

    except Exception as e:
        print(f"[SemanticSearch] 生成展示理由失败: {str(e)}")

    # 如果LLM调用失败，返回空字典
    return {}


@router.post("/semantic-search", response_model=BaseResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    对话式语义搜索用户

    流程：
    1. 调用 LLM 对用户输入进行语义改写和扩展，得到 3 条近似搜索语句
    2. 调用豆包 embedding 向量模型，得到语义对应的向量
    3. 基于向量在用户画像数据库中进行向量检索，得到最相近的备选用户
    4. 返回搜索结果
    """
    try:
        # 初始化服务
        llm_service = LLMService(db)
        profile_service = UserProfileService(db)

        print(f"[SemanticSearch] 开始语义搜索，用户查询: {request.query}")

        # 步骤1：使用 LLM 扩展查询
        print(f"[SemanticSearch] 步骤1：调用LLM扩展查询...")
        expanded_queries = await expand_query_with_llm(request.query, llm_service)
        print(f"[SemanticSearch] 扩展后的查询: {expanded_queries}")

        # 步骤2：使用 embedding 模型生成查询向量
        print(f"[SemanticSearch] 步骤2：调用embedding模型生成向量...")
        combined_query = f"{request.query} {' '.join(expanded_queries)}"
        embedding = await embedding_service.generate_embedding_with_retry(combined_query)

        if not embedding:
            print(f"[SemanticSearch] embedding生成失败")
            embedding = await embedding_service.generate_embedding_with_retry(request.query)
            if not embedding:
                return BaseResponse(
                    code=0,
                    message="success",
                    data={
                        "items": [],
                        "expanded_queries": [request.query],
                        "display_reasons": {},
                        "total": 0
                    }
                )

        # 步骤3：向量检索
        print(f"[SemanticSearch] 步骤3：执行向量检索...")
        exclude_user_ids = []
        if current_user:
            user_id = current_user.get("id")
            if user_id:
                exclude_user_ids = [user_id]

        limit = request.page_size
        offset = (request.page - 1) * request.page_size
        search_limit = offset + limit + 10

        candidates = profile_service.search_by_vector_similarity(
            embedding=embedding,
            exclude_user_ids=exclude_user_ids,
            limit=search_limit
        )

        print(f"[SemanticSearch] 向量检索找到 {len(candidates)} 个候选用户")

        paginated_candidates = candidates[offset:offset + limit]
        total = len(candidates)

        # 步骤4：获取用户详细信息
        print(f"[SemanticSearch] 步骤4：获取用户详细信息...")
        data_service = DataService()
        items = []

        for candidate in paginated_candidates:
            user_id = candidate['user_id']

            user_data = data_service.get_user_by_id(user_id)
            if not user_data:
                continue

            avatar_url = user_data.get('avatar_url') or user_data.get('avatarUrl', '')
            if avatar_url:
                avatar_url = ensure_full_url(avatar_url)

            item = SemanticSearchItem(
                user_id=user_id,
                name=user_data.get('nick_name') or user_data.get('nickName'),
                avatar_url=avatar_url,
                bio=user_data.get('bio'),
                gender=user_data.get('gender'),
                age=user_data.get('age'),
                location=user_data.get('location'),
                occupation=user_data.get('occupation'),
                interests=user_data.get('interests') or [],
                similarity=candidate['similarity']
            )
            items.append(item)

        response_data = SemanticSearchResponse(
            items=[item.dict() for item in items],
            expanded_queries=expanded_queries,
            display_reasons={},
            total=total
        )

        print(f"[SemanticSearch] 语义搜索完成，返回 {len(items)} 个结果")

        return BaseResponse(
            code=0,
            message="success",
            data=response_data.dict()
        )

    except Exception as e:
        print(f"[SemanticSearch] 语义搜索失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"搜索失败: {str(e)}",
            data={
                "items": [],
                "expanded_queries": [],
                "display_reasons": {},
                "total": 0
            }
        )


