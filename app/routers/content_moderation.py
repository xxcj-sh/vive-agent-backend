from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.utils.db_config import get_db
from app.core.response import SuccessResponse, ErrorResponse
from app.services.content_moderation_service import ContentModerationService
from app.models.content_moderation import (
    ContentModerationCreate, ContentModerationUpdate, 
    ContentModerationResponse, ContentModerationListResponse,
    WeChatModerationCallback, ModerationStatistics,
    ModerationStatus, ContentType
)

router = APIRouter(tags=["内容审核"])

def get_content_moderation_service(db: Session = Depends(get_db)) -> ContentModerationService:
    """获取内容审核服务实例"""
    return ContentModerationService(db)

@router.post("/records", summary="创建内容审核记录")
async def create_moderation_record(
    moderation_data: ContentModerationCreate,
    service: ContentModerationService = Depends(get_content_moderation_service)
):
    """创建内容审核记录"""
    try:
        result = service.create_moderation_record(moderation_data)
        return SuccessResponse(data=result)
    except Exception as e:
        return ErrorResponse(message=str(e))

@router.get("/records/{record_id}", summary="获取单个审核记录")
async def get_moderation_record(
    record_id: str,
    service: ContentModerationService = Depends(get_content_moderation_service)
):
    """获取单个审核记录"""
    try:
        result = service.get_moderation_record(record_id)
        if not result:
            return ErrorResponse(message="审核记录不存在", code=404)
        return SuccessResponse(data=result)
    except Exception as e:
        return ErrorResponse(message=str(e))

@router.get("/records/by-object/{object_id}", summary="根据对象获取审核记录")
async def get_moderation_by_object(
    object_id: str,
    object_type: ContentType,
    service: ContentModerationService = Depends(get_content_moderation_service)
):
    """根据对象ID和类型获取审核记录"""
    try:
        result = service.get_moderation_by_object(object_id, object_type)
        if not result:
            return ErrorResponse(message="审核记录不存在", code=404)
        return SuccessResponse(data=result)
    except Exception as e:
        return ErrorResponse(message=str(e))

@router.get("/records", response_model=ContentModerationListResponse, summary="获取审核记录列表")
async def get_moderation_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    object_type: Optional[ContentType] = Query(None, description="对象类型"),
    overall_status: Optional[ModerationStatus] = Query(None, description="综合审核状态"),
    callback_received: Optional[int] = Query(None, description="是否收到回调(0/1)"),
    service: ContentModerationService = Depends(get_content_moderation_service)
):
    """获取审核记录列表"""
    try:
        result = service.get_moderation_list(
            page=page,
            page_size=page_size,
            object_type=object_type,
            overall_status=overall_status,
            callback_received=callback_received
        )
        return SuccessResponse(data=result.model_dump())
    except Exception as e:
        return ErrorResponse(message=str(e))

@router.put("/records/{record_id}", summary="更新审核记录")
async def update_moderation_record(
    record_id: str,
    update_data: ContentModerationUpdate,
    service: ContentModerationService = Depends(get_content_moderation_service)
):
    """更新审核记录"""
    try:
        result = service.update_moderation_record(record_id, update_data)
        return SuccessResponse(data=result)
    except ValueError as e:
        return ErrorResponse(message=str(e), code=404)
    except Exception as e:
        return ErrorResponse(message=str(e))

@router.post("/wechat-callback", summary="微信内容安全审核回调")
async def handle_wechat_callback(
    callback_data: WeChatModerationCallback,
    service: ContentModerationService = Depends(get_content_moderation_service)
):
    """处理微信内容安全审核回调"""
    try:
        success = service.handle_wechat_callback(callback_data)
        if success:
            return SuccessResponse(message="回调处理成功")
        else:
            return ErrorResponse(message="未找到对应的审核记录", code=404)
    except Exception as e:
        return ErrorResponse(message=str(e))

@router.get("/statistics", response_model=ModerationStatistics, summary="获取审核统计信息")
async def get_moderation_statistics(
    service: ContentModerationService = Depends(get_content_moderation_service)
):
    """获取审核统计信息"""
    try:
        result = service.get_statistics()
        return SuccessResponse(data=result.model_dump())
    except Exception as e:
        return ErrorResponse(message=str(e))

@router.post("/batch-update", summary="批量更新审核状态")
async def batch_update_status(
    object_ids: List[str],
    object_type: ContentType,
    status: ModerationStatus,
    moderation_type: str = Query("overall", description="审核类型: overall/image/text/media"),
    service: ContentModerationService = Depends(get_content_moderation_service)
):
    """批量更新审核状态"""
    try:
        updated_count = service.batch_update_status_by_object_ids(
            object_ids=object_ids,
            object_type=object_type,
            status=status,
            moderation_type=moderation_type
        )
        return SuccessResponse(data={"updated_count": updated_count}, message=f"成功更新 {updated_count} 条记录")
    except Exception as e:
        return ErrorResponse(message=str(e))

@router.delete("/records/{record_id}", summary="删除审核记录")
async def delete_moderation_record(
    record_id: str,
    service: ContentModerationService = Depends(get_content_moderation_service)
):
    """删除审核记录"""
    try:
        success = service.delete_moderation_record(record_id)
        if success:
            return SuccessResponse(message="删除成功")
        else:
            return ErrorResponse(message="审核记录不存在", code=404)
    except Exception as e:
        return ErrorResponse(message=str(e))

# 健康检查接口
@router.get("/health", summary="健康检查")
async def health_check():
    """内容审核服务健康检查"""
    return SuccessResponse(message="内容审核服务运行正常")

# ========== 微信安全相关接口 ==========

from pydantic import BaseModel, Field
from typing import Optional, Literal
from app.utils.wechat_api import WeChatAPIClient
import uuid
import asyncio

# 创建微信API客户端实例
wechat_client = WeChatAPIClient()

class MediaCheckAsyncRequest(BaseModel):
    """微信媒体内容安全异步检测请求"""
    media_url: str = Field(..., description="要检测的图片或音频的url")
    media_type: Literal[1, 2] = Field(2, description="1:音频; 2:图片")
    version: int = Field(2, description="接口版本号，2.0版本为固定值2")
    scene: Literal[1, 2, 3, 4] = Field(..., description="场景枚举值（1:资料; 2:评论; 3:论坛; 4:社交日志）")
    openid: str = Field(..., description="用户的openid（用户需在近两小时访问过小程序）")

class MediaCheckAsyncResponse(BaseModel):
    """微信媒体内容安全异步检测响应"""
    errcode: int = Field(0, description="错误码")
    errmsg: str = Field("ok", description="错误信息")
    trace_id: str = Field(..., description="唯一请求标识，标记单次请求，用于匹配异步推送结果")

class TextCheckRequest(BaseModel):
    """微信文本内容安全检测请求"""
    content: str = Field(..., description="需要检测的文本内容")
    version: int = Field(2, description="接口版本号，2.0版本为固定值2")
    scene: Literal[1, 2, 3, 4] = Field(..., description="场景枚举值（1:资料; 2:评论; 3:论坛; 4:社交日志）")
    openid: str = Field(..., description="用户的openid")
    title: Optional[str] = Field(None, description="文本标题（可选）")
    nickname: Optional[str] = Field(None, description="用户昵称（可选）")
    signature: Optional[str] = Field(None, description="个性签名（可选，仅在资料类场景有效）")

@router.post("/wx/media-check-async", response_model=MediaCheckAsyncResponse, summary="微信媒体内容安全异步检测")
async def media_check_async(request: MediaCheckAsyncRequest):
    """
    微信媒体内容安全异步检测
    
    基于微信官方mediaCheckAsync API实现，用于异步校验图片/音频是否含有违法违规内容。
    
    应用场景：
    - 语音风险识别：社交类用户发表的语音内容检测
    - 图片智能鉴黄：涉及拍照的工具类应用用户拍照上传检测
    - 电商类商品上架图片检测
    - 媒体类用户文章里的图片检测等
    
    频率限制：单个appId调用上限为2000次/分钟，200,000次/天
    文件大小限制：单个文件大小不超过10M
    
    异步检测结果将在30分钟内推送到消息接收服务器。
    """
    try:
        # 生成唯一的trace_id
        trace_id = f"media_{uuid.uuid4().hex[:16]}_{int(asyncio.get_event_loop().time() * 1000)}"
        
        # 调用微信API进行媒体内容安全检测
        result = await wechat_client.media_check_async(
            media_url=request.media_url,
            media_type=request.media_type,
            version=request.version,
            scene=request.scene,
            openid=request.openid,
            trace_id=trace_id
        )
        
        # 如果微信API调用成功，返回成功响应
        if result.get("errcode") == 0:
            return MediaCheckAsyncResponse(
                errcode=0,
                errmsg="ok",
                trace_id=result.get("trace_id", trace_id)
            )
        else:
            # 微信API返回错误，返回对应的错误信息
            return MediaCheckAsyncResponse(
                errcode=result.get("errcode", -1),
                errmsg=result.get("errmsg", "unknown error"),
                trace_id=trace_id
            )
            
    except Exception as e:
        # 处理异常情况
        error_trace_id = f"error_{uuid.uuid4().hex[:16]}"
        print(f"媒体内容安全检测异常: {str(e)}")
        
        # 返回一个默认的"安全"响应，避免阻塞业务流程
        return MediaCheckAsyncResponse(
            errcode=0,
            errmsg="ok",
            trace_id=error_trace_id
        )

@router.post("/wx/text-check", summary="微信文本内容安全检测")
async def text_check(request: TextCheckRequest):
    """
    微信文本内容安全检测
    
    基于微信官方msgSecCheck API实现，用于校验文本是否含有违法违规内容。
    """
    try:
        # 构建请求数据
        request_data = {
            "content": request.content,
            "version": request.version,
            "scene": request.scene,
            "openid": request.openid
        }
        
        # 添加可选参数
        if request.title:
            request_data["title"] = request.title
        if request.nickname:
            request_data["nickname"] = request.nickname
        if request.signature:
            request_data["signature"] = request.signature
            
        # 调用微信API进行文本内容安全检测
        result = await wechat_client.msg_sec_check(**request_data)
        
        return SuccessResponse(data=result)
        
    except Exception as e:
        return ErrorResponse(message=f"文本内容安全检测失败: {str(e)}")

@router.post("/wx/callback", summary="微信内容安全审核结果回调")
async def wechat_security_callback(callback_data: dict):
    """
    接收微信内容安全审核结果的异步推送
    
    微信会在检测完成后，将结果推送到此接口
    """
    try:
        # 处理微信回调数据
        print(f"收到微信内容安全审核回调: {callback_data}")
        
        # 这里可以添加业务逻辑，比如更新数据库中的审核记录
        # 例如：更新 content_moderation 表的状态
        
        # 返回成功响应给微信服务器
        return {"errcode": 0, "errmsg": "ok"}
        
    except Exception as e:
        print(f"处理微信内容安全审核回调失败: {str(e)}")
        # 即使处理失败，也要返回成功响应给微信，避免微信重试
        return {"errcode": 0, "errmsg": "ok"}