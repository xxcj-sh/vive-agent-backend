import os
from typing import Any, Dict, List, Optional
# 移除mock_data依赖，改用数据库
from app.services.db_service import (
    create_user, get_user, get_user_by_email, get_users, update_user, delete_user,
    create_match, get_match, get_matches, update_match, delete_match,
    add_match_detail, get_match_details
)
from sqlalchemy.orm import Session
from app.utils.db_config import get_db

class DataService:
    """数据服务适配器，根据环境选择使用模拟数据或数据库"""
    
    def __init__(self):
        """初始化数据服务"""
        self.env = os.getenv("ENVIRONMENT", "development")
        # 在开发环境中也使用mock服务，除非明确设置为生产环境
        self.use_mock = self.env in ["testing"]
        
        # 使用全局模拟数据服务实例
        # 移除mock_service依赖
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
    
    # 用户相关方法
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        if self.use_mock:
            return self.mock_service.create_user(user_data)
        else:
            user = self._with_db(create_user, user_data)
            return user.__dict__
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        if self.use_mock:
            return self.mock_service.get_user_by_id(user_id)
        else:
            try:
                user = self._with_db(get_user, user_id)
                if user:
                    # 将数据库字段映射回前端字段
                    user_dict = user.__dict__.copy()
                    # 移除SQLAlchemy内部字段
                    user_dict.pop('_sa_instance_state', None)
                    
                    # 字段映射：数据库字段名 -> 前端字段名
                    reverse_mapping = {
                        'nick_name': 'nickName',
                        'avatar_url': 'avatarUrl',
                        'match_type': 'matchType',
                        'user_role': 'userRole',
                        'join_date': 'joinDate'
                    }
                    
                    # 应用反向映射
                    mapped_dict = {}
                    for db_field, value in user_dict.items():
                        frontend_field = reverse_mapping.get(db_field, db_field)
                        mapped_dict[frontend_field] = value
                    
                    return mapped_dict
                return None
            except Exception as e:

                return None
    
    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """根据token获取用户信息"""
        if self.use_mock:
            return self.mock_service.get_user_by_token(token)
        else:
            # 在实际应用中，这里应该解析token并获取用户ID
            # 简化示例，假设token就是用户ID
            try:
                user = self._with_db(get_user, token)
                if user:
                    # 将数据库字段映射回前端字段
                    user_dict = user.__dict__.copy()
                    # 移除SQLAlchemy内部字段
                    user_dict.pop('_sa_instance_state', None)
                    
                    # 字段映射：数据库字段名 -> 前端字段名
                    reverse_mapping = {
                        'nick_name': 'nickName',
                        'avatar_url': 'avatarUrl',
                        'match_type': 'matchType',
                        'user_role': 'userRole',
                        'join_date': 'joinDate'
                    }
                    
                    # 应用反向映射
                    mapped_dict = {}
                    for db_field, value in user_dict.items():
                        frontend_field = reverse_mapping.get(db_field, db_field)
                        mapped_dict[frontend_field] = value
                    
                    return mapped_dict
                return None
            except Exception as e:

                return None
    
    def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新用户资料"""
        if self.use_mock:
            return self.mock_service.update_profile(user_id, profile_data)
        else:
            try:

                
                user = self._with_db(update_user, user_id, profile_data)
                if user:
                    # 将数据库字段映射回前端字段
                    user_dict = user.__dict__.copy()
                    # 移除SQLAlchemy内部字段
                    user_dict.pop('_sa_instance_state', None)
                    

                    
                    # 字段映射：数据库字段名 -> 前端字段名
                    reverse_mapping = {
                        'nick_name': 'nickName',
                        'avatar_url': 'avatarUrl',
                        'match_type': 'matchType',
                        'user_role': 'userRole',
                        'join_date': 'joinDate'
                    }
                    
                    # 应用反向映射
                    mapped_dict = {}
                    for db_field, value in user_dict.items():
                        frontend_field = reverse_mapping.get(db_field, db_field)
                        mapped_dict[frontend_field] = value
                    

                    return mapped_dict
                return None
            except Exception as e:

                return None
    
    # 卡片和匹配相关方法
    def create_card(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建卡片"""
        if self.use_mock:
            return self.mock_service.create_card(card_data)
        else:
            # 在实际应用中，卡片可能是用户资料的一部分
            # 这里简化处理，将卡片作为匹配记录
            import uuid
            match_id = str(uuid.uuid4())
            
            match_data = {
                "id": match_id,
                "user_id": str(card_data.get("id", "unknown")),
                "match_type": card_data.get("matchType", "unknown"),
                "status": "active",
                "score": 0.0
            }
            
            # 提取详情
            details = []
            for key, value in card_data.items():
                if key not in ["id", "matchType", "status", "score"]:
                    details.append({
                        "detail_type": key,
                        "detail_value": str(value) if value is not None else ""
                    })
            
            match = self._with_db(create_match, match_data, details)
            return {**match.__dict__, "id": match.id}
    
    def get_cards(self, match_type: str, user_role: str, page: int, page_size: int) -> Dict[str, Any]:
        """获取匹配卡片"""
        if self.use_mock:
            return self.mock_service.get_cards(match_type, user_role, page, page_size)
        else:
            matches = self._with_db(get_matches, None, page - 1, page_size)
            
            # 转换为卡片格式
            cards = []
            for match in matches:
                card = {
                    "id": match.id,
                    "matchType": match.match_type,
                    "status": match.status,
                    "score": match.score
                }
                
                # 添加详情
                details = self._with_db(get_match_details, match.id)
                for detail in details:
                    card[detail.detail_type] = detail.detail_value
                
                cards.append(card)
            
            return {
                "total": len(cards),
                "list": cards,
                "page": page,
                "pageSize": page_size
            }
    
    def create_match(self, user_id: str, card_id: str, action: str) -> Dict[str, Any]:
        """创建匹配"""
        if self.use_mock:
            return self.mock_service.create_match(user_id, card_id, action)
        else:
            try:
                # 简化处理，直接创建匹配记录
                if action == "like":
                    import uuid
                    match_id = str(uuid.uuid4())
                    
                    match_data = {
                        "id": match_id,
                        "user_id": user_id,
                        "match_type": "dating",  # 默认类型
                        "status": "matched",
                        "score": 85.0  # 默认分数
                    }
                    
                    match = self._with_db(create_match, match_data)
                    
                    # 添加详情
                    detail_data = {
                        "detail_type": "card_id",
                        "detail_value": card_id
                    }
                    self._with_db(add_match_detail, match.id, detail_data)
                    
                    return {
                        "isMatch": True,
                        "matchId": match.id
                    }
                else:
                    return {
                        "isMatch": False,
                        "matchId": None
                    }
            except Exception as e:

                return {
                    "isMatch": False,
                    "matchId": None
                }
    
    def get_matches(self, user_id: str, status: str, page: int, page_size: int) -> Dict[str, Any]:
        """获取匹配列表"""
        if self.use_mock:
            return self.mock_service.get_matches(user_id, status, page, page_size)
        else:
            try:
                matches = self._with_db(get_matches, user_id, page - 1, page_size)
                
                # 转换为API格式
                match_list = []
                for match in matches:
                    match_dict = {
                        "id": match.id,
                        "userId1": user_id,
                        "userId2": "unknown",  # 默认值
                        "reason": "",
                        "createTime": int(match.created_at.timestamp()) if match.created_at else 0,
                        "isRead": True,
                        "type": match.match_type,
                        "status": match.status
                    }
                    
                    # 获取详情
                    details = self._with_db(get_match_details, match.id)
                    card_info = {}
                    for detail in details:
                        if detail.detail_type == "card_id":
                            match_dict["userId2"] = detail.detail_value
                        else:
                            card_info[detail.detail_type] = detail.detail_value
                    
                    match_dict["cardInfo"] = card_info
                    match_list.append(match_dict)
                
                return {
                    "total": len(match_list),
                    "list": match_list,
                    "page": page,
                    "pageSize": page_size
                }
            except Exception as e:

                return {
                    "total": 0,
                    "list": [],
                    "page": page,
                    "pageSize": page_size
                }
    
    def get_match_by_id(self, match_id: str, user_id: str = None) -> Dict[str, Any]:
        """根据ID获取匹配"""
        if self.use_mock:
            return self.mock_service.get_match_by_id(match_id, user_id)
        else:
            try:
                match = self._with_db(get_match, match_id)
                if not match:
                    return {}
                
                match_dict = {
                    "id": match.id,
                    "userId1": match.user_id,
                    "userId2": "unknown",  # 默认值
                    "reason": "",
                    "createTime": int(match.created_at.timestamp()) if match.created_at else 0,
                    "isRead": True,
                    "type": match.match_type,
                    "status": match.status
                }
                
                # 获取详情
                details = self._with_db(get_match_details, match.id)
                card_info = {}
                for detail in details:
                    if detail.detail_type == "card_id":
                        match_dict["userId2"] = detail.detail_value
                    else:
                        card_info[detail.detail_type] = detail.detail_value
                
                match_dict["cardInfo"] = card_info
                return match_dict
            except Exception as e:

                return {}
    
    # 聊天相关方法 - 这些方法在数据库版本中需要额外实现
    def get_chat_history(self, match_id: str, page: int, page_size: int) -> Dict[str, Any]:
        """获取聊天记录"""
        if self.use_mock:
            return self.mock_service.get_chat_history(match_id, page, page_size)
        else:
            # 在实际应用中，需要实现聊天记录的数据库模型和服务
            # 这里返回空列表作为占位符
            return {
                "total": 0,
                "list": [],
                "page": page,
                "pageSize": page_size
            }
    
    def send_message(self, match_id: str, sender_id: str, content: str, msg_type: str) -> Dict[str, Any]:
        """发送消息"""
        if self.use_mock:
            return self.mock_service.send_message(match_id, sender_id, content, msg_type)
        else:
            # 在实际应用中，需要实现消息的数据库模型和服务
            # 这里返回一个模拟的消息对象作为占位符
            import time
            return {
                "id": f"msg_{int(time.time())}",
                "content": content,
                "type": msg_type,
                "senderId": sender_id,
                "senderAvatar": "",
                "senderName": "",
                "timestamp": int(time.time()),
                "isRead": False
            }
    
    def upload_file(self, file_type: str) -> Dict[str, Any]:
        """上传文件"""
        if self.use_mock:
            return self.mock_service.upload_file(file_type)
        else:
            # 在实际应用中，需要实现文件上传服务
            # 这里返回一个模拟的URL作为占位符
            import uuid
            return {
                "url": f"https://example.com/uploads/{file_type}/{uuid.uuid4()}"
            }

# 创建数据服务实例
data_service = DataService()