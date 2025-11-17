# 统一响应模型
from pydantic import BaseModel
from typing import Any, Optional, Generic, TypeVar

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None
    
    class Config:
        json_encoders = {
            # 可以添加自定义的JSON编码器
        }

class SuccessResponse(BaseResponse[T]):
    """成功响应"""
    code: int = 0
    message: str = "success"

class ErrorResponse(BaseResponse[T]):
    """错误响应"""
    code: int = 500
    message: str = "error"
    
class PaginatedResponse(BaseResponse[T]):
    """分页响应"""
    code: int = 0
    message: str = "success"
    data: T
    total: int
    page: int
    page_size: int
    total_pages: int