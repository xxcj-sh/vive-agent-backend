from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.content_moderation_db import ContentModeration, ModerationStatus, ContentType
from app.models.content_moderation import (
    ContentModerationCreate, ContentModerationUpdate, 
    ContentModerationResponse, ContentModerationListResponse,
    WeChatModerationCallback, ModerationStatistics
)
import uuid
from datetime import datetime

class ContentModerationService:
    """内容审核服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_moderation_record(self, moderation_data: ContentModerationCreate) -> ContentModerationResponse:
        """创建内容审核记录"""
        try:
            # 检查是否已存在相同对象ID和类型的记录
            existing_record = self.db.query(ContentModeration).filter(
                and_(
                    ContentModeration.object_id == moderation_data.object_id,
                    ContentModeration.object_type == moderation_data.object_type
                )
            ).first()
            
            if existing_record:
                # 如果已存在，更新记录
                return self.update_moderation_record(existing_record.id, moderation_data)
            
            # 创建新记录
            moderation_record = ContentModeration(**moderation_data.model_dump())
            self.db.add(moderation_record)
            self.db.commit()
            self.db.refresh(moderation_record)
            
            return ContentModerationResponse.model_validate(moderation_record)
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"创建内容审核记录失败: {str(e)}")
    
    def update_moderation_record(self, record_id: str, update_data: ContentModerationUpdate) -> ContentModerationResponse:
        """更新内容审核记录"""
        try:
            moderation_record = self.db.query(ContentModeration).filter(
                ContentModeration.id == record_id
            ).first()
            
            if not moderation_record:
                raise ValueError("审核记录不存在")
            
            # 更新字段
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(moderation_record, field, value)
            
            # 如果更新了任何审核状态，重新计算综合状态
            if any(field in update_dict for field in [
                'image_status', 'text_status', 'media_status', 'overall_status'
            ]):
                moderation_record.result_updated_at = func.now()
                if 'overall_status' not in update_dict:
                    moderation_record.update_overall_status()
            
            self.db.commit()
            self.db.refresh(moderation_record)
            
            return ContentModerationResponse.model_validate(moderation_record)
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"更新内容审核记录失败: {str(e)}")
    
    def get_moderation_record(self, record_id: str) -> Optional[ContentModerationResponse]:
        """获取单个审核记录"""
        try:
            moderation_record = self.db.query(ContentModeration).filter(
                ContentModeration.id == record_id
            ).first()
            
            if not moderation_record:
                return None
            
            return ContentModerationResponse.model_validate(moderation_record)
            
        except Exception as e:
            raise Exception(f"获取审核记录失败: {str(e)}")
    
    def get_moderation_by_object(self, object_id: str, object_type: ContentType) -> Optional[ContentModerationResponse]:
        """根据对象ID和类型获取审核记录"""
        try:
            moderation_record = self.db.query(ContentModeration).filter(
                and_(
                    ContentModeration.object_id == object_id,
                    ContentModeration.object_type == object_type
                )
            ).first()
            
            if not moderation_record:
                return None
            
            return ContentModerationResponse.model_validate(moderation_record)
            
        except Exception as e:
            raise Exception(f"获取对象审核记录失败: {str(e)}")
    
    def get_moderation_list(
        self, 
        page: int = 1, 
        page_size: int = 10,
        object_type: Optional[ContentType] = None,
        overall_status: Optional[ModerationStatus] = None,
        callback_received: Optional[int] = None
    ) -> ContentModerationListResponse:
        """获取审核记录列表"""
        try:
            query = self.db.query(ContentModeration)
            
            # 应用筛选条件
            if object_type:
                query = query.filter(ContentModeration.object_type == object_type)
            if overall_status:
                query = query.filter(ContentModeration.overall_status == overall_status)
            if callback_received is not None:
                query = query.filter(ContentModeration.callback_received == callback_received)
            
            # 获取总数
            total = query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            records = query.order_by(ContentModeration.created_at.desc()).offset(offset).limit(page_size).all()
            
            # 转换为响应模型
            items = [ContentModerationResponse.model_validate(record) for record in records]
            
            return ContentModerationListResponse(
                total=total,
                items=items,
                page=page,
                page_size=page_size,
                total_pages=(total + page_size - 1) // page_size
            )
            
        except Exception as e:
            raise Exception(f"获取审核记录列表失败: {str(e)}")
    
    def handle_wechat_callback(self, callback_data: WeChatModerationCallback) -> bool:
        """处理微信内容安全审核回调"""
        try:
            # 从回调数据中提取trace_id
            trace_id = callback_data.trace_id
            
            # 根据trace_id查找对应的审核记录
            # 注意：这里假设trace_id与我们的image_trace_id、text_trace_id或media_trace_id匹配
            moderation_record = self.db.query(ContentModeration).filter(
                or_(
                    ContentModeration.image_trace_id == trace_id,
                    ContentModeration.text_trace_id == trace_id,
                    ContentModeration.media_trace_id == trace_id
                )
            ).first()
            
            if not moderation_record:
                print(f"未找到对应的审核记录，trace_id: {trace_id}")
                return False
            
            # 根据trace_id判断是哪种类型的审核回调
            if moderation_record.image_trace_id == trace_id:
                moderation_record.image_status = callback_data.status
                moderation_record.image_moderation_result = callback_data.detail
            elif moderation_record.text_trace_id == trace_id:
                moderation_record.text_status = callback_data.status
                moderation_record.text_moderation_result = callback_data.detail
            elif moderation_record.media_trace_id == trace_id:
                moderation_record.media_status = callback_data.status
                moderation_record.media_moderation_result = callback_data.detail
            
            # 更新回调相关信息
            moderation_record.callback_received = 1
            moderation_record.callback_time = datetime.now()
            moderation_record.callback_data = callback_data.model_dump()
            
            # 更新综合审核状态
            moderation_record.update_overall_status()
            moderation_record.result_updated_at = func.now()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"处理微信审核回调失败: {str(e)}")
            return False
    
    def get_statistics(self) -> ModerationStatistics:
        """获取审核统计信息"""
        try:
            total_count = self.db.query(ContentModeration).count()
            
            pending_count = self.db.query(ContentModeration).filter(
                ContentModeration.overall_status == ModerationStatus.PENDING
            ).count()
            
            pass_count = self.db.query(ContentModeration).filter(
                ContentModeration.overall_status == ModerationStatus.PASS
            ).count()
            
            reject_count = self.db.query(ContentModeration).filter(
                ContentModeration.overall_status == ModerationStatus.REJECT
            ).count()
            
            review_count = self.db.query(ContentModeration).filter(
                ContentModeration.overall_status == ModerationStatus.REVIEW
            ).count()
            
            callback_received_count = self.db.query(ContentModeration).filter(
                ContentModeration.callback_received == 1
            ).count()
            
            return ModerationStatistics(
                total_count=total_count,
                pending_count=pending_count,
                pass_count=pass_count,
                reject_count=reject_count,
                review_count=review_count,
                callback_received_count=callback_received_count
            )
            
        except Exception as e:
            raise Exception(f"获取审核统计信息失败: {str(e)}")
    
    def batch_update_status_by_object_ids(
        self, 
        object_ids: List[str], 
        object_type: ContentType,
        status: ModerationStatus,
        moderation_type: str = "overall"
    ) -> int:
        """批量更新审核状态"""
        try:
            query = self.db.query(ContentModeration).filter(
                and_(
                    ContentModeration.object_id.in_(object_ids),
                    ContentModeration.object_type == object_type
                )
            )
            
            update_data = {
                "result_updated_at": func.now()
            }
            
            if moderation_type == "overall":
                update_data["overall_status"] = status
            elif moderation_type == "image":
                update_data["image_status"] = status
            elif moderation_type == "text":
                update_data["text_status"] = status
            elif moderation_type == "media":
                update_data["media_status"] = status
            
            updated_count = query.update(update_data)
            self.db.commit()
            
            return updated_count
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"批量更新审核状态失败: {str(e)}")
    
    def delete_moderation_record(self, record_id: str) -> bool:
        """删除审核记录（软删除）"""
        try:
            moderation_record = self.db.query(ContentModeration).filter(
                ContentModeration.id == record_id
            ).first()
            
            if not moderation_record:
                return False
            
            # 物理删除，因为审核记录通常需要保留用于审计
            self.db.delete(moderation_record)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"删除审核记录失败: {str(e)}")