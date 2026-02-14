"""
微信小程序码 API
用于生成小程序码和小程序二维码
"""

import httpx
from fastapi import APIRouter, HTTPException, Request
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from app.config import settings
import json

router = APIRouter()


def parse_bool(value: Any) -> bool:
    """解析布尔值，支持字符串 'true'/'false'"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes')
    return bool(value)


class WxacodeParams(BaseModel):
    """获取小程序码参数"""
    scene: str = Field(..., description="场景值，最大32个可见字符")
    page: str = Field(default="pages/user-preview/user-preview", description="页面路径")
    width: int = Field(default=430, ge=28, le=1280, description="二维码的宽度")
    auto_color: Union[bool, str] = Field(default=False, description="自动配置线条颜色")
    line_color: Optional[Dict[str, Any]] = Field(default=None, description="线条颜色")
    is_hyaline: Union[bool, str] = Field(default=False, description="是否需要透明底色")
    
    class Config:
        extra = "ignore"
        
    @property
    def auto_color_bool(self) -> bool:
        return parse_bool(self.auto_color)
    
    @property
    def is_hyaline_bool(self) -> bool:
        return parse_bool(self.is_hyaline)


async def get_stable_access_token(force_refresh: bool = False) -> Optional[str]:
    """
    获取微信 access_token
    """
    url = "https://api.weixin.qq.com/cgi-bin/token"
    
    params = {
        "grant_type": "client_credential",
        "appid": settings.WECHAT_APP_ID,
        "secret": settings.WECHAT_APP_SECRET
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if "access_token" in data:
                return data["access_token"]
            else:
                error_code = data.get("errcode")
                error_msg = data.get("errmsg", "未知错误")
                print(f"[WxacodeAPI] 获取 access_token 失败: {error_code} - {error_msg}")
                return None
                
    except Exception as e:
        print(f"[WxacodeAPI] 获取 access_token 异常: {e}")
        return None


@router.post("/wechat/wxacode/getUnlimited")
async def get_wxacode_unlimited(request: Request, params: WxacodeParams = None):
    """
    获取不限制的小程序码
    """
    print(f"[WxacodeAPI] 收到请求: scene={params.scene if params else 'None'}")
    
    if params is None:
        raise HTTPException(status_code=400, detail="参数解析失败")
    
    access_token = await get_stable_access_token()
    
    if not access_token:
        raise HTTPException(status_code=500, detail="无法获取 access_token")
    
    url = f"https://api.weixin.qq.com/wxa/getwxacodeunlimit?access_token={access_token}"
    
    payload = {
        "scene": params.scene,
        "page": params.page,
        "width": params.width,
        "auto_color": params.auto_color_bool,
        "is_hyaline": params.is_hyaline_bool
    }
    
    if params.line_color:
        payload["line_color"] = params.line_color
    
    print(f"[WxacodeAPI] 调用微信 API...")
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload)
        
        # 检查响应内容
        try:
            error_data = response.json()
            if "errcode" in error_data:
                errcode = error_data.get("errcode")
                errmsg = error_data.get("errmsg", "未知错误")
                print(f"[WxacodeAPI] 微信错误: {errcode} - {errmsg}")
                raise HTTPException(status_code=400, detail=f"微信 API 错误: {errmsg}")
        except (json.JSONDecodeError, ValueError):
            pass
        
        if len(response.content) > 0:
            from fastapi.responses import Response
            return Response(
                content=response.content,
                media_type="image/png",
                headers={"Content-Disposition": f'attachment; filename="wxacode_{params.scene}.png"'}
            )
        else:
            raise HTTPException(status_code=500, detail="空响应")


@router.get("/wechat/wxacode/access-token")
async def get_access_token_info():
    """获取 access_token 信息"""
    access_token = await get_stable_access_token()
    if access_token:
        return {"success": True, "access_token": access_token}
    else:
        return {"success": False, "message": "获取失败"}
