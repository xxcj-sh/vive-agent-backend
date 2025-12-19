from typing import Optional, Dict, Any
from app.config import settings
from app.models.schemas import UserInfo
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
# 实际生产环境的微信API调用
import httpx
import json

# 延迟导入避免循环依赖
from app.models.user import User
from sqlalchemy.orm import Session
from app.utils.db_config import get_db

def create_user_func(db: Session, user_data: Dict[str, Any]) -> User:
    """创建用户"""
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_phone_func(db: Session, phone: str) -> Optional[User]:
    """根据手机号获取用户"""
    return db.query(User).filter(User.phone == phone).first()

def get_user_func(db: Session, user_id: str) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()

def get_db_services():
    return create_user_func, get_user_by_phone_func, get_user_func

class AuthService:
    """认证服务 - 只使用数据库"""
    
    @staticmethod
    def verify_wx_code(code: str) -> Optional[Dict[str, str]]:
        """验证微信登录code
        
        调用微信API进行验证
        """
        # 开发模式：返回模拟数据
        if settings.DEBUG:
            print(f"[开发模式] 模拟微信code验证，code: {code}")
            # 模拟返回openid和session_key
            import uuid
            return {
                "openid": f"debug_openid_{uuid.uuid4().hex[:16]}",
                "session_key": f"debug_session_{uuid.uuid4().hex[:16]}",
                "unionid": f"debug_unionid_{uuid.uuid4().hex[:16]}"
            }
        try:
            # 微信官方API: https://api.weixin.qq.com/sns/jscode2session
            url = "https://api.weixin.qq.com/sns/jscode2session"
            params = {
                "appid": settings.WECHAT_APP_ID,
                "secret": settings.WECHAT_APP_SECRET,
                "js_code": code,
                "grant_type": "authorization_code"
            }
            
            # 发送请求到微信API
            response = httpx.get(url, params=params, timeout=10)
            result = response.json()
            
            # 检查错误码
            if "errcode" in result and result["errcode"] != 0:
                error_msg = result.get("errmsg", "微信API调用失败")
                print(f"微信API错误: {error_msg}, 错误码: {result['errcode']}")
                
                # 根据错误码提供具体错误信息
                if result["errcode"] == 40163:
                    raise ValueError("微信code已过期，请重新获取")
                elif result["errcode"] == 40164:
                    raise ValueError("无效的IP地址")
                elif result["errcode"] == 40029:
                    raise ValueError("无效的微信code")
                elif result["errcode"] == 45011:
                    raise ValueError("微信API调用频繁，请稍后再试")
                else:
                    raise ValueError(f"微信验证失败: {error_msg}")
            
            # 验证返回数据
            if "openid" not in result:
                raise ValueError("微信API返回数据异常")
            
            print(f"微信code验证成功，openid: {result['openid']}")
            return {
                "openid": result["openid"],
                "session_key": result.get("session_key", ""),
                "unionid": result.get("unionid", "")
            }
            
        except httpx.RequestError as e:
            print(f"微信API网络请求失败: {e}")
            raise ValueError("微信服务连接失败，请检查网络")
        except json.JSONDecodeError as e:
            print(f"微信API返回数据解析失败: {e}")
            raise ValueError("微信服务返回异常数据")
        except Exception as e:
            print(f"微信code验证异常: {e}")
            raise ValueError(f"微信验证失败: {str(e)}")
    
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
            from app.models.user import User
            
            db = SessionLocal()
            try:
                user = get_user_func(db, user_id)
                if user and user.status != 'deleted':  # 只返回非删除状态的用户
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
        is_new_user = None
        
        # 使用数据库
        if db:
            create_user_func, get_user_by_phone_func, get_user_func = get_db_services()
            db_user = get_user_by_phone_func(db, phone)
            if db_user:
                # 检查用户是否为新用户：如果用户已存在且有注册时间，则为老用户
                is_new_user = not (hasattr(db_user, 'register_at') and db_user.register_at)
                user_dict = {
                    "id": db_user.id,
                    "phone": db_user.phone,
                    "nickName": db_user.nick_name,
                    "avatarUrl": db_user.avatar_url,
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
                    "avatar_url": "",
                    "gender": 0,
                    "is_active": True,
                    "status": "active",
                    "register_at": datetime.now()
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
    def login_by_wechat_phone(code: str, phone_code: str, user_info: Optional[UserInfo] = None, db: Optional[Session] = None) -> Dict[str, Any]:
        """微信一键登录（获取手机号）"""
        # 验证微信code
        wx_result = AuthService.verify_wx_code(code)
        if not wx_result:
            raise ValueError("无效的微信code")
        
        # 验证手机号code（这里需要调用微信API获取真实手机号）
        phone_result = AuthService.verify_wx_phone_code(phone_code)
        if not phone_result:
            raise ValueError("无效的手机号授权")
        
        phone = phone_result.get("phoneNumber")
        if not phone:
            raise ValueError("无法获取手机号")
        
        openid = wx_result["openid"]
        
        user_dict = None
        is_new_user = None
        
        # 使用数据库
        if db:
            create_user_func, get_user_by_phone_func, get_user_func = get_db_services()
            db_user = get_user_by_phone_func(db, phone)
            
            if db_user:
                # 用户已存在，更新微信信息
                is_new_user = not (hasattr(db_user, 'register_at') and db_user.register_at)
                
                # 如果有用户信息，更新用户资料
                if user_info:
                    if user_info.nick_name and not db_user.nick_name:
                        db_user.nick_name = user_info.nick_name
                    if user_info.avatar_url and not db_user.avatar_url:
                        db_user.avatar_url = user_info.avatar_url
                    if user_info.gender is not None and db_user.gender is None:
                        db_user.gender = user_info.gender
                
                # 更新微信openid
                db_user.wechat_open_id = openid
                
                user_dict = {
                    "id": db_user.id,
                    "phone": db_user.phone,
                    "nickName": db_user.nick_name,
                    "avatarUrl": db_user.avatar_url,
                    "gender": db_user.gender or 0
                }
            else:
                # 新用户，创建用户记录
                is_new_user = True
                user_id = str(uuid.uuid4())
                
                user_data = {
                    "id": user_id,
                    "phone": phone,
                    "nick_name": user_info.nick_name if user_info and user_info.nick_name else f"用户{phone[-4:]}",
                    "avatar_url": user_info.avatar_url if user_info and user_info.avatar_url else "",
                    "gender": user_info.gender if user_info and user_info.gender is not None else 0,
                    "wechat_open_id": openid,
                    "is_active": True,
                    "status": "active",
                    "register_at": datetime.now()
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
                "gender": user_dict["gender"],
                "phone": user_dict["phone"]
            }
        }
    
    @staticmethod
    def verify_wx_phone_code(phone_code: str) -> Optional[Dict[str, Any]]:
        """验证微信手机号授权code
        
        在实际生产环境中，这里应该调用微信API获取真实手机号
        """
        # 开发模式：模拟手机号获取
        if settings.DEBUG:
            # 模拟返回手机号，实际应该调用微信API
            import random
            phone_prefix = ['138', '139', '158', '159', '188', '189']
            phone = random.choice(phone_prefix) + ''.join([str(random.randint(0, 9)) for _ in range(8)])
            print(f"[开发模式] 模拟获取手机号: {phone}")
            return {
                "phoneNumber": phone,
                "purePhoneNumber": phone,
                "countryCode": "86"
            }
        
        # 生产模式：调用微信手机号获取API
        try:
            # 获取access_token
            access_token = AuthService._get_wx_access_token()
            if not access_token:
                raise ValueError("无法获取微信访问令牌")
            
            # 调用微信手机号获取API
            url = f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={access_token}"
            
            payload = {
                "code": phone_code
            }
            
            response = httpx.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # 检查返回结果
            if result.get("errcode") != 0:
                error_msg = result.get("errmsg", "未知错误")
                error_code = result.get("errcode")
                
                # 根据错误码提供更详细的错误信息
                if error_code == 40163:
                    raise ValueError("手机号授权码已过期，请重新获取")
                elif error_code == 40164:
                    raise ValueError("无效的IP地址，请检查服务器配置")
                elif error_code == 40001:
                    raise ValueError("无效的access_token，请重试")
                elif error_code == 40003:
                    raise ValueError("无效的openid，请检查用户授权")
                else:
                    raise ValueError(f"微信手机号获取失败: {error_msg}")
            
            # 返回手机号信息
            phone_info = result.get("phone_info", {})
            if not phone_info:
                raise ValueError("无法从微信获取手机号信息")
            
            return {
                "phoneNumber": phone_info.get("phoneNumber"),
                "purePhoneNumber": phone_info.get("purePhoneNumber"),
                "countryCode": phone_info.get("countryCode", "86")
            }
            
        except httpx.RequestError as e:
            raise ValueError(f"网络请求失败: {str(e)}")
        except httpx.TimeoutException:
            raise ValueError("微信API请求超时，请重试")
        except json.JSONDecodeError:
            raise ValueError("微信API返回数据格式错误")
        except Exception as e:
            raise ValueError(f"微信手机号获取异常: {str(e)}")
    
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
        print("user_data:", user_data)
        # 使用数据库
        if db:
            create_user_func, get_user_by_phone_func = get_db_services()
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
                "is_active": True,
                "status": "active",  # 注册成功后设置为激活状态
                "register_at": datetime.now()  # 设置注册时间
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

    @staticmethod
    def get_anonymous_user() -> Dict[str, Any]:
        """获取匿名用户信息"""
        import uuid
        return {
            "id": f"anonymous_{uuid.uuid4().hex[:16]}",
            "nickName": "匿名用户",
            "avatarUrl": "",
            "gender": 0,
            "phone": "",
            "is_anonymous": True
        }

    @staticmethod
    def _get_wx_access_token() -> Optional[str]:
        """获取微信访问令牌"""
        try:
            # 调用微信access_token获取API
            url = f"https://api.weixin.qq.com/cgi-bin/token"
            params = {
                "grant_type": "client_credential",
                "appid": settings.WECHAT_APP_ID,
                "secret": settings.WECHAT_APP_SECRET
            }
            
            response = httpx.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            # 检查返回结果
            if "access_token" in result:
                return result["access_token"]
            else:
                error_code = result.get("errcode")
                error_msg = result.get("errmsg", "未知错误")
                print(f"获取微信access_token失败: 错误码 {error_code}, 错误信息: {error_msg}")
                return None
                
        except httpx.RequestError as e:
            print(f"获取微信access_token网络请求失败: {str(e)}")
            return None
        except httpx.TimeoutException:
            print(f"获取微信access_token请求超时")
            return None
        except json.JSONDecodeError:
            print(f"获取微信access_token返回数据格式错误")
            return None
        except Exception as e:
            print(f"获取微信access_token异常: {str(e)}")
            return None

    @staticmethod
    def dev_quick_login(phone: str, db: Session) -> Dict[str, Any]:
        """开发者快速登录（仅开发环境）"""
        try:
            # 检查是否为开发环境
            if not settings.DEBUG:
                raise ValueError("该接口仅在开发环境可用")
            
            # 验证手机号格式
            if not phone or not phone.startswith('1') or len(phone) != 11:
                raise ValueError("手机号格式不正确")
            
            create_user_func, get_user_by_phone_func, get_user_func = get_db_services()
            
            # 检查用户是否已存在
            existing_user = get_user_by_phone_func(db, phone)
            
            if existing_user:
                # 用户存在，直接登录
                user_dict = {
                    "id": existing_user.id,
                    "phone": existing_user.phone,
                    "nickName": existing_user.nick_name,
                    "avatarUrl": existing_user.avatar_url,
                    "gender": existing_user.gender
                }
                print(f"[开发者登录] 用户已存在，手机号: {phone}, 用户ID: {existing_user.id}")
            else:
                # 用户不存在，创建新用户
                user_id = str(uuid.uuid4())
                new_user_data = {
                    "id": user_id,
                    "phone": phone,
                    "nick_name": f"开发用户{phone[-4:]}",
                    "avatar_url": f"https://picsum.photos/200/200?random=dev{phone[-4:]}",
                    "gender": 0,
                    "is_active": True,
                    "status": "active",
                    "register_at": datetime.now()
                }
                
                db_user = create_user_func(db, new_user_data)
                user_dict = {
                    "id": db_user.id,
                    "phone": db_user.phone,
                    "nickName": db_user.nick_name,
                    "avatarUrl": db_user.avatar_url,
                    "gender": db_user.gender
                }
                print(f"[开发者登录] 创建新用户，手机号: {phone}, 用户ID: {user_id}")
            
            # 创建token
            token = AuthService.create_token(str(user_dict["id"]))
            
            return {
                "token": token,
                "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "userInfo": {
                    "id": user_dict["id"],
                    "nickName": user_dict["nickName"],
                    "avatarUrl": user_dict["avatarUrl"],
                    "gender": user_dict["gender"]
                }
            }
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"开发者登录失败: {str(e)}")

auth_service = AuthService()