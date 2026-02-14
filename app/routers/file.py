"""
文件上传路由
处理文件上传相关的API请求
"""

import os
import uuid
import shutil
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.models.schemas import BaseResponse
from app.dependencies import get_current_user
from app.config import settings
from pathlib import Path

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """测试端点，检查路由是否正常"""
    return BaseResponse(
        code=0,
        message="文件路由正常工作",
        data={"timestamp": "2025-09-01", "status": "ok"}
    )

@router.post("/test-form")
async def test_form_endpoint(
    test_field: str = Form(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """测试表单数据接收"""
    return BaseResponse(
        code=0,
        message="表单数据接收正常",
        data={
            "received_field": test_field,
            "user": str(current_user)
        }
    )

# 允许的文件类型
ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4", "video/avi", "video/mov", "video/wmv", "video/flv", "video/webm"
}

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf", "application/msword", 
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain"
}

ALL_ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_DOCUMENT_TYPES


def validate_file_type(file: UploadFile, allowed_types: set) -> bool:
    """验证文件类型"""
    return file.content_type in allowed_types


def validate_file_size(file: UploadFile, max_size: int) -> bool:
    """验证文件大小"""
    if hasattr(file, 'size') and file.size:
        return file.size <= max_size
    return True  # 如果无法获取大小，允许上传


def get_file_extension(filename: str) -> str:
    """获取文件扩展名"""
    return Path(filename).suffix.lower()


def generate_unique_filename(original_filename: str) -> str:
    """生成唯一的文件名"""
    ext = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{ext}"


def save_uploaded_file(file: UploadFile, user_id: str, file_type: str) -> dict:
    """保存上传的文件"""
    try:
        # 创建用户专属目录
        user_dir = os.path.join(settings.UPLOAD_DIR, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        # 生成唯一文件名
        unique_filename = generate_unique_filename(file.filename or "unknown")
        file_path = os.path.join(user_dir, unique_filename)
        
        # 保存文件
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 生成访问URL
        relative_path = os.path.join(user_id, unique_filename).replace('\\', '/')
        file_url = f"/uploads/{relative_path}"
        
        return {
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": file_path,
            "file_url": file_url,
            "file_size": file_size,
            "file_type": file_type,
            "content_type": file.content_type
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(default="image"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    上传文件
    
    Args:
        file: 上传的文件
        file_type: 文件类型 (image, video, document)
        current_user: 当前用户
    
    Returns:
        上传结果
    """
    try:
        # 详细的调试信息
        print(f"=== 文件上传调试信息 ===")
        print(f"文件对象: {file}")
        print(f"文件名: {file.filename if file else 'None'}")
        print(f"文件类型参数: {file_type}")
        print(f"内容类型: {file.content_type if file else 'None'}")
        print(f"当前用户: {current_user}")
        print(f"用户ID: {getattr(current_user, 'id', 'None')}")
        
        # 验证文件是否存在
        if not file:
            print("错误: 没有接收到文件对象")
            raise HTTPException(status_code=400, detail="没有接收到文件")
            
        if not file.filename:
            print("错误: 文件名为空")
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 检查文件内容类型
        print(f"文件内容类型: {file.content_type}")
        
        # 智能文件类型检测 - 根据实际内容类型自动判断
        actual_file_type = None
        if file.content_type in ALLOWED_IMAGE_TYPES:
            actual_file_type = "image"
            max_size = settings.MAX_IMAGE_SIZE
        elif file.content_type in ALLOWED_VIDEO_TYPES:
            actual_file_type = "video"
            max_size = settings.MAX_VIDEO_SIZE
        elif file.content_type in ALLOWED_DOCUMENT_TYPES:
            actual_file_type = "document"
            max_size = settings.MAX_FILE_SIZE
        else:
            print(f"不支持的文件类型: {file.content_type}")
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式 '{file.content_type}'。支持的格式: 图片({', '.join(ALLOWED_IMAGE_TYPES)})，视频({', '.join(ALLOWED_VIDEO_TYPES)})，文档({', '.join(ALLOWED_DOCUMENT_TYPES)})"
            )
        
        print(f"检测到的文件类型: {actual_file_type}")
        print(f"用户指定的类型: {file_type}")
        
        # 如果用户指定的类型与实际类型不匹配，使用实际类型
        if file_type != actual_file_type:
            print(f"类型不匹配，使用实际检测到的类型: {actual_file_type}")
            file_type = actual_file_type
        
        # 验证文件大小
        print(f"验证文件大小，限制: {max_size} bytes ({max_size/(1024*1024):.1f}MB)")
        if hasattr(file, 'size') and file.size:
            print(f"文件大小: {file.size} bytes ({file.size/(1024*1024):.2f}MB)")
        
        if not validate_file_size(file, max_size):
            max_size_mb = max_size / (1024 * 1024)
            actual_size = getattr(file, 'size', 'unknown')
            print(f"文件大小验证失败: {actual_size} > {max_size}")
            raise HTTPException(
                status_code=400, 
                detail=f"文件大小超过限制 ({max_size_mb:.1f}MB)，当前文件大小: {actual_size}"
            )
        
        # 获取用户ID - 尝试多个可能的字段名
        user_id = current_user.get('id') or current_user.get('user_id') or current_user.get('phone', 'anonymous')
        if not user_id:
            user_id = 'anonymous'
        
        print(f"最终用户ID: {user_id}")
        
        # 保存文件
        file_info = save_uploaded_file(file, user_id, file_type)
        
        return BaseResponse(
            code=0,
            message="文件上传成功",
            data=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"文件上传异常: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/upload/simple")
async def upload_file_simple(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """简化版文件上传，用于调试"""
    try:
        print(f"=== 简化版文件上传 ===")
        print(f"文件: {file}")
        print(f"文件名: {file.filename}")
        print(f"内容类型: {file.content_type}")
        print(f"用户: {current_user}")
        
        if not file or not file.filename:
            return BaseResponse(code=400, message="文件或文件名为空", data=None)
        
        # 简单保存到临时位置
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        return BaseResponse(
            code=0,
            message="简化上传成功",
            data={
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content),
                "temp_path": tmp_path
            }
        )
        
    except Exception as e:
        print(f"简化上传错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(code=500, message=f"上传失败: {str(e)}", data=None)

@router.post("/upload/multiple")
def upload_multiple_files(
    files: List[UploadFile] = File(...),
    file_type: str = Form(default="image"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    批量上传文件
    
    Args:
        files: 上传的文件列表
        file_type: 文件类型
        current_user: 当前用户
    
    Returns:
        批量上传结果
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="未选择文件")
        
        # 限制批量上传数量
        max_files = 10
        if len(files) > max_files:
            raise HTTPException(status_code=400, detail=f"一次最多上传{max_files}个文件")
        
        results = []
        errors = []
        
        for i, file in enumerate(files):
            try:
                # 重用单文件上传逻辑
                user_id = current_user.get('id') or current_user.get('user_id') or current_user.get('phone', 'anonymous')
                file_info = save_uploaded_file(
                    file, 
                    user_id, 
                    file_type
                )
                results.append(file_info)
                
            except Exception as e:
                errors.append({
                    "file_index": i,
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return BaseResponse(
            code=0,
            message=f"批量上传完成，成功{len(results)}个，失败{len(errors)}个",
            data={
                "success_files": results,
                "failed_files": errors,
                "total": len(files),
                "success_count": len(results),
                "error_count": len(errors)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"批量文件上传异常: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"批量文件上传失败: {str(e)}")


@router.delete("/delete/{file_path:path}")
def delete_file(
    file_path: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    删除文件
    
    Args:
        file_path: 文件路径
        current_user: 当前用户
    
    Returns:
        删除结果
    """
    try:
        user_id = current_user.get('id') or current_user.get('user_id') or current_user.get('phone', 'anonymous')
        
        # 构建完整文件路径
        full_path = os.path.join(settings.UPLOAD_DIR, file_path)
        
        # 安全检查：确保文件在用户目录下
        if not file_path.startswith(user_id):
            raise HTTPException(status_code=403, detail="无权限删除此文件")
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 删除文件
        os.remove(full_path)
        
        return BaseResponse(
            code=0,
            message="文件删除成功",
            data={"deleted_file": file_path}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"文件删除异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")


@router.get("/info/{file_path:path}")
def get_file_info(
    file_path: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
        current_user: 当前用户
    
    Returns:
        文件信息
    """
    try:
        user_id = getattr(current_user, 'id', 'anonymous')
        
        # 构建完整文件路径
        full_path = os.path.join(settings.UPLOAD_DIR, file_path)
        
        # 安全检查
        if not file_path.startswith(user_id):
            raise HTTPException(status_code=403, detail="无权限访问此文件")
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取文件信息
        stat = os.stat(full_path)
        file_info = {
            "file_path": file_path,
            "file_size": stat.st_size,
            "created_time": stat.st_ctime,
            "modified_time": stat.st_mtime,
            "file_url": f"/uploads/{file_path.replace(os.sep, '/')}"
        }
        
        return BaseResponse(
            code=0,
            message="获取文件信息成功",
            data=file_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取文件信息异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")