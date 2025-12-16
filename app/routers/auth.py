from fastapi import APIRouter, Depends, HTTPException, Request, Form
from app.models.schemas import (
    BaseResponse, 
    LoginRequest, 
    LoginResponse,
    UserInfo
)
from app.models.user import LoginRequest as UserLoginRequest, RegisterRequest
from app.services.auth import auth_service, AuthService
from app.utils.auth import get_current_user
from app.dependencies import get_auth_service
from app.utils.db_config import get_db
from sqlalchemy.orm import Session
from pydantic import ValidationError, BaseModel
from typing import Dict, Any
from app.config import settings

router = APIRouter()

# 开发者快速登录请求模型
class DevQuickLoginRequest(BaseModel):
    phone: str

@router.post("/sessions", response_model=BaseResponse, status_code=201)
async def login(
    request: Request,
    auth_service = Depends(get_auth_service)
):
    try:
        # Parse the request body manually to catch validation errors
        body = await request.json()
        
        # Check if code is provided in the request
        if "code" not in body:
            return BaseResponse(code=422, message="缺少code参数", data={})
        
        # Check if code is empty
        if not body["code"] or not isinstance(body["code"], str) or not body["code"].strip():
            return BaseResponse(code=422, message="code不能为空", data={})
        
        # Create user_info if provided
        user_info = None
        if "userInfo" in body and isinstance(body["userInfo"], dict):
            try:
                user_info = UserInfo(
                    nick_name=body["userInfo"].get("nickName"),
                    avatar_url=body["userInfo"].get("avatarUrl"),
                    gender=body["userInfo"].get("gender")
                )
            except:
                pass
        
        # 验证登录请求
        login_result = auth_service.login(
            code=body["code"],
            user_info=user_info
        )
        
        # 构建响应数据
        return BaseResponse(
            code=0,
            message="success",
            data={
                "token": login_result["token"],
                "expiresIn": login_result["expiresIn"],
                "isNewUser": login_result.get("isNewUser", False),
                "userInfo": login_result["userInfo"]
            }
        )
    except ValidationError as e:
        # Handle validation errors specifically
        return BaseResponse(code=422, message="验证错误", data={})
    except ValueError as e:
        # Handle value errors
        return BaseResponse(code=422, message=str(e), data={})
    except Exception as e:
        return BaseResponse(code=1001, message=str(e), data={})

@router.post("/sessions/wechat-phone", response_model=BaseResponse, status_code=201)
async def login_by_wechat_phone(
    request: Request,
    db: Session = Depends(get_db),
    auth_service = Depends(get_auth_service)
):
    """微信一键登录（获取手机号）"""
    try:
        body = await request.json()
        code = body.get("code")
        phone_code = body.get("phoneCode")
        user_info = body.get("userInfo")
        
        if not code or not phone_code:
            return BaseResponse(code=422, message="缺少必要参数", data={})
        
        # Create user_info if provided
        user_info_obj = None
        if user_info and isinstance(user_info, dict):
            try:
                user_info_obj = UserInfo(
                    nick_name=user_info.get("nickName"),
                    avatar_url=user_info.get("avatarUrl"),
                    gender=user_info.get("gender")
                )
            except:
                pass
        
        # 调用微信一键登录服务
        login_result = auth_service.login_by_wechat_phone(
            code=code,
            phone_code=phone_code,
            user_info=user_info_obj,
            db=db
        )
        
        return BaseResponse(
            code=0,
            message="success",
            data={
                "token": login_result["token"],
                "expiresIn": login_result["expiresIn"],
                "isNewUser": login_result.get("isNewUser", False),
                "userInfo": login_result["userInfo"]
            }
        )
    except ValueError as e:
        return BaseResponse(code=422, message=str(e), data={})
    except Exception as e:
        return BaseResponse(code=1006, message=f"微信一键登录失败: {str(e)}", data={})

@router.post("/sessions/phone", response_model=BaseResponse, status_code=201)
async def login_by_phone(
    request: Request,
    db: Session = Depends(get_db),
    auth_service = Depends(get_auth_service)
):
    try:
        body = await request.json()
        phone = body.get("phone")
        code = body.get("code")
        
        if not phone or not code:
            return BaseResponse(code=422, message="缺少必要参数", data={})
        
        # 打印验证码信息到控制台
        print(f"[验证码验证] 手机号: {phone}, 验证码: {code}")
        
        login_result = AuthService.login_by_phone(phone, code, db)
        
        return BaseResponse(
            code=0,
            message="success",
            data={
                "token": login_result["token"],
                "expiresIn": login_result["expiresIn"],
                "isNewUser": login_result.get("isNewUser", False),
                "userInfo": login_result["userInfo"]
            }
        )
    except Exception as e:
        raise e
        return BaseResponse(code=1002, message=str(e), data={})

@router.post("/sms-codes", response_model=BaseResponse, status_code=201)
async def send_sms_code(
    request: Request
):
    try:
        body = await request.json()
        phone = body.get("phone")
        
        if not phone:
            return BaseResponse(code=422, message="缺少手机号", data={})
        
        # In test mode, just return success
        return BaseResponse(
            code=0,
            message="success",
            data={"sent": True}
        )
    except Exception as e:
        return BaseResponse(code=1003, message=str(e), data={})

@router.post("/sms/send", response_model=BaseResponse, status_code=201)
async def send_sms_code_alt(
    request: Request
):
    try:
        body = await request.json()
        phone = body.get("phone")
        
        if not phone:
            return BaseResponse(code=422, message="缺少手机号", data={})
        
        # In test mode, just return success
        return BaseResponse(
            code=0,
            message="success",
            data={"sent": True}
        )
    except Exception as e:
        return BaseResponse(code=1003, message=str(e), data={})

@router.get("/validate", response_model=BaseResponse)
async def validate_token(request: Request):
    """验证Token有效性"""
    try:
        # 获取Authorization头
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return BaseResponse(code=401, message="未提供有效的认证信息", data={})
        
        token = auth_header.split(" ")[1]
        
        # 简化的Token验证：直接从数据库查找用户
        from app.utils.db_config import SessionLocal
        from app.models.user import User
        
        db = SessionLocal()
        try:
            # token就是用户ID，直接查找
            db_user = db.query(User).filter(User.id == token).first()
            if db_user:
                return BaseResponse(
                    code=0,
                    message="Token有效",
                    data={
                        "valid": True,
                        "userInfo": {
                            "id": db_user.id,
                            "nickName": db_user.nick_name,
                            "avatarUrl": db_user.avatar_url,
                            "gender": db_user.gender or 0
                        }
                    }
                )
            else:
                return BaseResponse(code=401, message="无效的token", data={})
        finally:
            db.close()
            
    except Exception as e:
        return BaseResponse(code=500, message=f"Token验证失败: {str(e)}", data={})

@router.get("/sessions/current", response_model=BaseResponse)
async def get_current_session(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # 获取当前会话信息
    return BaseResponse(
        code=0,
        message="success",
        data={
            "valid": True,
            "user": {
                "id": current_user.get("id"),
                "nickName": current_user.get("nickName")
            }
        }
    )

@router.post("/register", response_model=BaseResponse, status_code=201)
async def register(
    request: Request,
    db: Session = Depends(get_db),
    auth_service = Depends(get_auth_service)
):
    """用户注册"""
    try:
        body = await request.json()
        phone = body.get("phone")
        verification_code = body.get("verificationCode")  # 修正参数名
        nick_name = body.get("nickName")  # 修正参数名
        
        if not phone or not verification_code:
            return BaseResponse(code=422, message="手机号和验证码不能为空", data={})
        
        user_data = {
            "phone": phone,
            "verification_code": verification_code,
            "nick_name": nick_name
        }
        
        register_result = AuthService.register(user_data, db)
        
        return BaseResponse(
            code=0,
            message="注册成功",
            data={
                "token": register_result["token"],
                "expiresIn": register_result["expiresIn"],
                "userInfo": register_result["userInfo"]
            }
        )
    except ValueError as e:
        return BaseResponse(code=1004, message=str(e), data={})
    except Exception as e:
        return BaseResponse(code=1005, message=f"注册失败: {str(e)}", data={})

@router.delete("/sessions/current", status_code=204)
async def logout():
    # 登出操作 - 204状态码不能有响应体
    pass

@router.post("/sessions/dev-quick-login", response_model=BaseResponse, status_code=201)
async def dev_quick_login(
    request: DevQuickLoginRequest,
    db: Session = Depends(get_db),
    auth_service = Depends(get_auth_service)
):
    """开发者快速登录（仅开发环境）"""
    try:
        # 检查是否为开发环境
        if not settings.DEBUG:
            return BaseResponse(code=403, message="该接口仅在开发环境可用", data={})
        
        phone = request.phone
        if not phone:
            return BaseResponse(code=422, message="手机号不能为空", data={})
        
        # 验证手机号格式 - 限定为测试手机号，首位数字为0
        if not phone.startswith('100') or len(phone) != 11:
            return BaseResponse(code=422, message="仅限测试手机号（首位为100）", data={})
        
        # 调用服务层的开发者快速登录方法
        login_result = AuthService.dev_quick_login(phone, db)
        
        return BaseResponse(
            code=0,
            message="开发者登录成功",
            data={
                "token": login_result["token"],
                "expiresIn": login_result["expiresIn"],
                "userInfo": login_result["userInfo"]
            }
        )
    except ValueError as e:
        return BaseResponse(code=422, message=str(e), data={})
    except Exception as e:
        return BaseResponse(code=1006, message=f"开发者登录失败: {str(e)}", data={})