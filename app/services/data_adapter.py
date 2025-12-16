import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.utils.db_config import get_db
from app.models.user import User

class DataService:
    """数据服务适配器 - 始终使用数据库"""
    
    def __init__(self):
        """初始化数据服务"""
        pass
    
    def _get_db(self):
        """获取数据库会话生成器"""
        return get_db()
    
    def _with_db(self, func, *args, **kwargs):
        """使用数据库会话执行函数"""
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            return func(db, *args, **kwargs)
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        try:
            db_gen = self._get_db()
            db = next(db_gen)
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    # 移除SQLAlchemy内部字段并返回干净的字典
                    user_dict = user.__dict__.copy()
                    user_dict.pop('_sa_instance_state', None)
                    return user_dict
                return None
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass
        except Exception as e:
            print(f"获取用户失败: {e}")
            return None
    
    def get_cards(self, match_type: str, user_role: str, page: int, page_size: int) -> Dict[str, Any]:
        """获取卡片列表 - 简化实现"""
        # 这是一个简化实现，实际业务逻辑可能需要更复杂的查询
        return {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": 0
            },
            "list": []
        }