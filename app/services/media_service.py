"""
媒体服务
负责处理用户的多媒体数据，包括头像、图片、视频等
"""

from typing import Dict, List, Any, Optional
import os
import random
from app.utils.db_config import get_db
from sqlalchemy.orm import Session

class MediaService:
    """媒体服务类"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
        self.upload_base_path = "uploads"
    
    def get_user_media(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的多媒体数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            包含用户多媒体数据的字典
        """
        try:
            # 实际实现中应该从数据库查询用户的媒体文件
            # 这里提供示例实现
            
            # 检查用户上传目录
            user_upload_path = os.path.join(self.upload_base_path, user_id)
            
            media_data = {
                "avatar_url": "",
                "video_url": "",
                "images": [],
                "house_images": [],
                "house_video_url": ""
            }
            
            if os.path.exists(user_upload_path):
                # 扫描用户上传的文件
                media_data = self._scan_user_media_files(user_upload_path, user_id)
            else:
                # 如果没有上传文件，生成示例数据
                media_data = self._generate_default_media_data(user_id)
            
            return media_data
            
        except Exception as e:
            print(f"获取用户媒体数据失败: {str(e)}")
            return self._generate_default_media_data(user_id)
    
    def _scan_user_media_files(self, user_path: str, user_id: str) -> Dict[str, Any]:
        """扫描用户上传的媒体文件"""
        media_data = {
            "avatar_url": "",
            "video_url": "",
            "images": [],
            "house_images": [],
            "house_video_url": ""
        }
        
        try:
            for root, dirs, files in os.walk(user_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.upload_base_path)
                    file_url = f"/uploads/{relative_path.replace(os.sep, '/')}"
                    
                    # 根据文件名和路径分类
                    if "avatar" in file.lower():
                        media_data["avatar_url"] = file_url
                    elif "house" in file.lower() and file.lower().endswith(('.mp4', '.avi', '.mov')):
                        media_data["house_video_url"] = file_url
                    elif "house" in file.lower() and file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        media_data["house_images"].append(file_url)
                    elif file.lower().endswith(('.mp4', '.avi', '.mov')):
                        media_data["video_url"] = file_url
                    elif file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        media_data["images"].append(file_url)
            
            # 如果没有头像，使用第一张图片作为头像
            if not media_data["avatar_url"] and media_data["images"]:
                media_data["avatar_url"] = media_data["images"][0]
                
        except Exception as e:
            print(f"扫描用户媒体文件失败: {str(e)}")
        
        return media_data
    
    def _generate_default_media_data(self, user_id: str) -> Dict[str, Any]:
        """生成默认的媒体数据"""
        return {
            "avatar_url": f"https://images.unsplash.com/photo-{random.randint(1500000000, 1700000000)}-{random.randint(100000000, 999999999)}?w=400&h=400&fit=crop&crop=face",
            "video_url": "",
            "images": [
                f"https://images.unsplash.com/photo-{random.randint(1500000000, 1700000000)}-{random.randint(100000000, 999999999)}?w=400&h=600&fit=crop&random={user_id}_1",
                f"https://images.unsplash.com/photo-{random.randint(1500000000, 1700000000)}-{random.randint(100000000, 999999999)}?w=400&h=600&fit=crop&random={user_id}_2"
            ],
            "house_images": [
                "https://images.unsplash.com/photo-1522708323590-d2db1a6ee4ea?w=800&h=600&fit=crop",
                "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&h=600&fit=crop",
                "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800&h=600&fit=crop"
            ],
            "house_video_url": ""
        }
    
    def upload_media_file(self, user_id: str, file_data: bytes, filename: str, media_type: str = "image") -> str:
        """
        上传媒体文件
        
        Args:
            user_id: 用户ID
            file_data: 文件数据
            filename: 文件名
            media_type: 媒体类型 (image, video, avatar, house_image, house_video)
            
        Returns:
            上传后的文件URL
        """
        try:
            # 创建用户上传目录
            user_upload_path = os.path.join(self.upload_base_path, user_id)
            os.makedirs(user_upload_path, exist_ok=True)
            
            # 根据媒体类型确定文件路径
            if media_type == "avatar":
                file_path = os.path.join(user_upload_path, f"avatar_{filename}")
            elif media_type == "house_image":
                file_path = os.path.join(user_upload_path, f"house_{filename}")
            elif media_type == "house_video":
                file_path = os.path.join(user_upload_path, f"house_video_{filename}")
            else:
                file_path = os.path.join(user_upload_path, filename)
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # 返回文件URL
            relative_path = os.path.relpath(file_path, self.upload_base_path)
            return f"/uploads/{relative_path.replace(os.sep, '/')}"
            
        except Exception as e:
            print(f"上传媒体文件失败: {str(e)}")
            raise e
    
    def delete_media_file(self, user_id: str, file_url: str) -> bool:
        """
        删除媒体文件
        
        Args:
            user_id: 用户ID
            file_url: 文件URL
            
        Returns:
            是否删除成功
        """
        try:
            # 从URL提取文件路径
            if file_url.startswith("/uploads/"):
                file_path = os.path.join(self.upload_base_path, file_url[9:])
                
                # 验证文件属于该用户
                if user_id in file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    return True
            
            return False
            
        except Exception as e:
            print(f"删除媒体文件失败: {str(e)}")
            return False
    
    def get_media_file_info(self, file_url: str) -> Dict[str, Any]:
        """
        获取媒体文件信息
        
        Args:
            file_url: 文件URL
            
        Returns:
            文件信息字典
        """
        try:
            if file_url.startswith("/uploads/"):
                file_path = os.path.join(self.upload_base_path, file_url[9:])
                
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    return {
                        "url": file_url,
                        "size": stat.st_size,
                        "created_time": stat.st_ctime,
                        "modified_time": stat.st_mtime,
                        "exists": True
                    }
            
            return {"url": file_url, "exists": False}
            
        except Exception as e:
            print(f"获取媒体文件信息失败: {str(e)}")
            return {"url": file_url, "exists": False, "error": str(e)}

# 创建全局媒体服务实例
media_service = MediaService()