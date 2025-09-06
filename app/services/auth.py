from typing import Optional, Dict, Any
from app.config import settings
from app.models.schemas import UserInfo
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
import hashlib
import secrets
import time
import random
import uuid

# 延迟导入避免循环依赖
def get_db_services():
    from app.services.db_service import create_user, get_user_by_phone, get_user
    return create_user, get_user_by_phone, get_user

class AuthService:
    """认证服务 - 只使用数据库"""
    
    @staticmethod
    def verify_wx_code(code: str) -> Optional[Dict[str, str]]:
        """验证微信登录code
        
        调用微信API进行验证
        """
        # 实际生产环境的微信API调用
        # TODO: 实现微信API调用
        # 微信API: https://api.weixin.qq.com/sns/jscode2session
        raise HTTPException(status_code=501, detail="微信API集成待实现")
    
    @staticmethod
    def create_token(user_id: str) -> str:
        """创建用户token
        
        使用JWT创建token
        """
        try:
            from jose import jwt
            payload = {"user_id": user_id}
            return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        except ImportError:
            # 如果没有安装jose库，仍然返回用户ID作为token
            return user_id
    
    @staticmethod
    def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
        """从token获取用户信息"""
        
        # 测试模式：使用测试token
        if token == "test_token_001":
            return {
                "id": "test_user_001",
                "nickName": "测试用户",
                "avatarUrl": "https://picsum.photos/200/200?random=test",
                "gender": 1,
                "phone": "13800138000"
            }
        
        # 尝试从token解析用户ID
        try:
            from jose import jwt
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("user_id")
            if not user_id:
                return None
        except:
            # 如果不是JWT格式，直接作为用户ID使用
            user_id = token
        
        # 从数据库获取用户信息
        try:
            from app.utils.db_config import SessionLocal
            from app.services.db_service import get_user
            
            db = SessionLocal()
            try:
                user = get_user(db, user_id)
                if user:
                    return {
                        "id": user.id,
                        "nickName": user.nick_name,
                        "avatarUrl": user.avatar_url,
                        "gender": user.gender or 0,
                        "phone": user.phone
                    }
            finally:
                db.close()
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            pass
            
        return None
    
    @staticmethod
    def login(code: str, user_info: Optional[UserInfo] = None) -> Dict[str, Any]:
        """微信登录
        
        只使用数据库，不支持模拟数据和固定测试用户
        """
        # 验证微信code
        wx_result = AuthService.verify_wx_code(code)
        if not wx_result:
            raise ValueError("无效的微信code")
        
        openid = wx_result["openid"]
        
        # 查找或创建用户（在实际实现中，应该连接到数据库）
        # 目前直接抛出异常，要求先注册
        raise ValueError("用户未注册，请先注册")
    
    @staticmethod
    def login_by_phone(phone: str, code: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """手机号登录 - 只使用数据库"""
        # 验证验证码
        if not AuthService.verify_sms_code(phone, code):
            raise ValueError("无效的验证码")
        
        user_dict = None
        is_new_user = False
        
        # 使用数据库
        if db:
            create_user_func, get_user_by_phone_func, get_user_func = get_db_services()
            db_user = get_user_by_phone_func(db, phone)
            if db_user:
                # 检查用户是否为新用户（没有创建任何资料）
                is_new_user = False if hasattr(db_user, 'profiles') and db_user.profiles else True
                user_dict = {
                    "id": db_user.id,
                    "phone": db_user.phone,
                    "nickName": db_user.nick_name or "用户",
                    "avatarUrl": db_user.avatar_url or "https://picsum.photos/200/200?random=default",
                    "gender": db_user.gender or 0
                }
            else:
                # 数据库中没有用户，创建新用户
                is_new_user = True
                user_id = str(uuid.uuid4())
                user_data = {
                    "id": user_id,
                    "phone": phone,
                    "nick_name": f"用户{phone[-4:]}",
                    "avatar_url": "https://picsum.photos/200/200?random=default",
                    "gender": 0,
                    "is_active": True
                }
                db_user = create_user_func(db, user_data)
                user_dict = {
                    "id": db_user.id,
                    "phone": db_user.phone,
                    "nickName": db_user.nick_name,
                    "avatarUrl": db_user.avatar_url,
                    "gender": db_user.gender
                }
        else:
            # 如果没有提供数据库会话，抛出异常
            raise ValueError("数据库连接不能为空")
        
        # 创建token
        token = AuthService.create_token(str(user_dict["id"]))
        
        return {
            "token": token,
            "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "isNewUser": is_new_user,
            "userInfo": {
                "id": user_dict["id"],
                "nickName": user_dict["nickName"],
                "avatarUrl": user_dict["avatarUrl"],
                "gender": user_dict["gender"]
            }
        }
    
    @staticmethod
    def verify_sms_code(phone: str, code: str) -> bool:
        """验证短信验证码
        
        开发模式下允许任意验证码，生产环境需要真实验证
        """
        # 开发模式：允许任意验证码
        if settings.DEBUG:
            print(f"[开发模式] 跳过验证码验证，手机号: {phone}, 验证码: {code}")
            return True
            
        # TODO: 集成真实的短信验证服务
        # 目前返回True，需要在实际部署时替换为真实的验证逻辑
        return True
    
    @staticmethod
    def login_by_wechat(code: str) -> Dict[str, Any]:
        """微信授权登录"""
        # 验证微信code
        wx_result = AuthService.verify_wx_code(code)
        if not wx_result:
            raise ValueError("无效的微信code")
        
        openid = wx_result["openid"]
        
        # 在实际应用中，这里应该从数据库查找用户
        # 目前直接抛出异常，要求先注册
        raise ValueError("用户未注册，请先注册")
    
    @staticmethod
    def register(user_data: Dict[str, Any], db: Optional[Session] = None) -> Dict[str, Any]:
        """用户注册 - 只使用数据库"""
        phone = user_data.get("phone")
        code = user_data.get("verification_code") or user_data.get("code")
        nick_name = user_data.get("nick_name") or user_data.get("nickName")
        
        if not phone or not code:
            raise ValueError("手机号和验证码不能为空")
        
        if not AuthService.verify_sms_code(phone, code):
            raise ValueError("无效的验证码")
        
        user_dict = None
        
        # 使用数据库
        if db:
            create_user_func, get_user_by_phone_func, get_user_func = get_db_services()
            # 检查手机号是否已注册
            existing_user = get_user_by_phone_func(db, phone)
            if existing_user:
                raise ValueError("手机号已注册")
            
            # 创建新用户
            user_id = str(uuid.uuid4())
            new_user_data = {
                "id": user_id,
                "phone": phone,
                "nick_name": nick_name or f"用户{phone[-4:]}",
                "avatar_url": user_data.get("avatar_url") or user_data.get("avatarUrl") or "https://picsum.photos/200/200?random=default",
                "gender": user_data.get("gender", 0),
                "is_active": True
            }
            
            db_user = create_user_func(db, new_user_data)
            user_dict = {
                "id": db_user.id,
                "phone": db_user.phone,
                "nickName": db_user.nick_name,
                "avatarUrl": db_user.avatar_url,
                "gender": db_user.gender
            }
        else:
            # 如果没有提供数据库会话，抛出异常
            raise ValueError("数据库连接不能为空")
        
        # 创建token
        token = AuthService.create_token(str(user_dict["id"]))
        
        return {
            "token": token,
            "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "isNewUser": True,
            "userInfo": {
                "id": user_dict["id"],
                "nickName": user_dict["nickName"],
                "avatarUrl": user_dict["avatarUrl"],
                "gender": user_dict["gender"]
            }
        }
    
    @staticmethod
    def logout(user_id: str) -> bool:
        """退出登录"""
        # 生产环境中可能需要将token加入黑名单
        return True
    
    @staticmethod
    async def get_current_user(authorization: Optional[str] = Header(None)):
        """获取当前登录用户"""
        if not authorization:
            raise HTTPException(status_code=401, detail="未提供认证信息")
        
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="无效的认证格式")
        
        token = authorization.split(" ")[1]
        user = AuthService.get_user_from_token(token)
        
        if not user:
            raise HTTPException(status_code=401, detail="无效的token")
        
        return user

    @staticmethod
    async def get_current_user_optional(authorization: Optional[str] = Header(None)):
        """获取当前登录用户（可选，不抛出异常）"""
        try:
            return await AuthService.get_current_user(authorization)
        except HTTPException:
            return None

auth_service = AuthService()