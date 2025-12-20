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

router = APIRouter(prefix="/api/content-moderation", tags=["内容审核"])

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