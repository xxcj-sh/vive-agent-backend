from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from app.models.match_action import MatchAction, MatchResult, MatchActionType, MatchResultStatus
from app.models.user import User
from datetime import datetime
import uuid

class MatchService:
    """匹配服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def submit_match_action(self, user_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提交匹配操作
        
        Args:
            user_id: 当前用户ID
            action_data: 操作数据，包含cardId, action, matchType等
            
        Returns:
            包含匹配结果的字典
        """
        try:
            card_id = action_data.get("cardId")
            action_type = action_data.get("action")
            match_type = action_data.get("matchType")
            
            if not all([card_id, action_type, match_type]):
                raise ValueError("缺少必要参数: cardId, action, matchType")
            
            # 确保参数类型正确
            card_id = str(card_id)
            action_type = str(action_type)
            match_type = str(match_type)
            
            # 解析目标用户ID（从cardId中提取或查询）
            target_user_id = self._extract_target_user_id(card_id, match_type)
            
            if not target_user_id:
                raise ValueError(f"无法从cardId {card_id} 中获取目标用户ID")
            
            # 检查是否已经对该目标执行过操作
            existing_action = self.db.query(MatchAction).filter(
                MatchAction.user_id == user_id,
                MatchAction.target_user_id == target_user_id,
                MatchAction.target_card_id == card_id,
                MatchAction.match_type == match_type
            ).first()
            
            if existing_action:
                return {
                    "isMatch": False,
                    "message": "已经对该用户执行过操作",
                    "existingAction": existing_action.action_type.value
                }
            
            # 创建匹配操作记录
            match_action = MatchAction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                target_user_id=target_user_id,
                target_card_id=card_id,
                action_type=MatchActionType(action_type),
                match_type=match_type,
                scene_context=action_data.get("sceneContext")
            )
            
            self.db.add(match_action)
            self.db.commit()
            self.db.refresh(match_action)
            
            # 如果是喜欢或超级喜欢，检查是否形成双向匹配
            is_match = False
            match_id = None
            
            if action_type in ["like", "super_like"]:
                is_match, match_id = self._check_mutual_match(
                    user_id, target_user_id, card_id, match_type, str(match_action.id)
                )
            
            return {
                "isMatch": is_match,
                "matchId": match_id,
                "actionId": match_action.id,
                "message": "操作成功"
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"提交匹配操作失败: {str(e)}")
    
    def _extract_target_user_id(self, card_id: str, match_type: str) -> Optional[str]:
        """
        从卡片ID中提取目标用户ID
        
        Args:
            card_id: 卡片ID
            match_type: 匹配类型
            
        Returns:
            目标用户ID
        """
        # 根据不同的匹配类型，从不同的表中查询目标用户ID
        if match_type == "housing":
            # 对于房源匹配，可能需要从房源表或用户资料表中查询
            # 这里假设card_id就是用户资料ID，实际实现时需要根据具体业务逻辑调整
            from app.models.user_profile import UserProfile
            profile = self.db.query(UserProfile).filter(UserProfile.id == card_id).first()
            return str(profile.user_id) if profile else None
        
        elif match_type == "dating":
            # 对于交友匹配，card_id可能直接是用户ID或用户资料ID
            from app.models.user_profile import UserProfile
            profile = self.db.query(UserProfile).filter(UserProfile.id == card_id).first()
            return str(profile.user_id) if profile else None
        
        elif match_type == "activity":
            # 对于活动匹配，类似处理
            from app.models.user_profile import UserProfile
            profile = self.db.query(UserProfile).filter(UserProfile.id == card_id).first()
            return str(profile.user_id) if profile else None
        
        # 如果无法确定，尝试直接作为用户ID查询
        user = self.db.query(User).filter(User.id == card_id).first()
        return str(user.id) if user else None
    
    def _check_mutual_match(self, user_id: str, target_user_id: str, 
                           card_id: str, match_type: str, current_action_id: str) -> tuple[bool, Optional[str]]:
        """
        检查是否形成双向匹配
        
        Args:
            user_id: 当前用户ID
            target_user_id: 目标用户ID
            card_id: 卡片ID
            match_type: 匹配类型
            current_action_id: 当前操作ID
            
        Returns:
            (是否匹配, 匹配ID)
        """
        # 查找目标用户是否也对当前用户执行了喜欢操作
        target_action = self.db.query(MatchAction).filter(
            MatchAction.user_id == target_user_id,
            MatchAction.target_user_id == user_id,
            MatchAction.match_type == match_type,
            MatchAction.action_type.in_([MatchActionType.LIKE, MatchActionType.SUPER_LIKE])
        ).first()
        
        if target_action:
            # 检查是否已经存在匹配结果
            existing_match = self.db.query(MatchResult).filter(
                (
                    (MatchResult.user1_id == user_id) & 
                    (MatchResult.user2_id == target_user_id)
                ) | (
                    (MatchResult.user1_id == target_user_id) & 
                    (MatchResult.user2_id == user_id)
                ),
                MatchResult.match_type == match_type
            ).first()
            
            if existing_match:
                return True, str(existing_match.id)
            
            # 创建新的匹配结果
            # 确保user1_id < user2_id，保持一致的排序
            if user_id < target_user_id:
                user1_id, user2_id = user_id, target_user_id
                user1_action_id, user2_action_id = current_action_id, target_action.id
                user1_card_id, user2_card_id = card_id, target_action.target_card_id
            else:
                user1_id, user2_id = target_user_id, user_id
                user1_action_id, user2_action_id = target_action.id, current_action_id
                user1_card_id, user2_card_id = target_action.target_card_id, card_id
            
            match_result = MatchResult(
                id=str(uuid.uuid4()),
                user1_id=user1_id,
                user2_id=user2_id,
                user1_card_id=user1_card_id,
                user2_card_id=user2_card_id,
                match_type=match_type,
                status=MatchResultStatus.MATCHED,
                user1_action_id=user1_action_id,
                user2_action_id=user2_action_id
            )
            
            self.db.add(match_result)
            self.db.commit()
            self.db.refresh(match_result)
            
            return True, str(match_result.id)
        
        return False, None
    
    def get_user_matches(self, user_id: str, status: str = "all", 
                        page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        获取用户的匹配列表
        
        Args:
            user_id: 用户ID
            status: 状态筛选
            page: 页码
            page_size: 每页数量
            
        Returns:
            匹配列表数据
        """
        query = self.db.query(MatchResult).filter(
            (MatchResult.user1_id == user_id) | (MatchResult.user2_id == user_id)
        )
        
        if status != "all":
            if status == "new":
                # 使用 SQL 表达式进行比较
                from sqlalchemy import text
                query = query.filter(text("last_activity_at = matched_at"))
            elif status == "contacted":
                from sqlalchemy import text
                query = query.filter(text("last_activity_at > matched_at"))
        
        # 分页
        total = query.count()
        matches = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 构建返回数据
        match_list = []
        for match in matches:
            # 确定对方用户
            other_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
            other_user = self.db.query(User).filter(User.id == other_user_id).first()
            
            if other_user:
                match_list.append({
                    "id": match.id,
                    "user": {
                        "id": other_user.id,
                        "name": other_user.nick_name or "匿名用户",
                        "avatar": other_user.avatar_url
                    },
                    "matchedAt": match.matched_at.isoformat(),
                    "lastActivity": match.last_activity_at.isoformat(),
                    "matchType": match.match_type,
                    "status": match.status.value
                })
        
        return {
            "matches": match_list,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": (total + page_size - 1) // page_size
            }
        }
    
    def get_match_detail(self, match_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取匹配详情
        
        Args:
            match_id: 匹配ID
            user_id: 当前用户ID
            
        Returns:
            匹配详情数据
        """
        match = self.db.query(MatchResult).filter(
            MatchResult.id == match_id
        ).filter(
            (MatchResult.user1_id == user_id) | (MatchResult.user2_id == user_id)
        ).first()
        
        if not match:
            return None
        
        # 确定对方用户
        other_user_id = match.user2_id if match.user1_id == user_id else match.user1_id
        other_user = self.db.query(User).filter(User.id == other_user_id).first()
        
        if not other_user:
            return None
        
        return {
            "id": match.id,
            "user": {
                "id": other_user.id,
                "name": other_user.nick_name or "匿名用户",
                "avatar": other_user.avatar_url,
                "age": other_user.age,
                "location": other_user.location,
                "occupation": other_user.occupation,
                "bio": other_user.bio
            },
            "matchedAt": match.matched_at.isoformat(),
            "matchType": match.match_type,
            "status": match.status.value,
            "reason": self._generate_match_reason(match)
        }
    
    def _generate_match_reason(self, match: MatchResult) -> str:
        """
        生成匹配原因描述
        
        Args:
            match: 匹配结果对象
            
        Returns:
            匹配原因描述
        """
        if match.match_type == "housing":
            return "你们都在寻找合适的住房"
        elif match.match_type == "dating":
            return "你们互相感兴趣"
        elif match.match_type == "activity":
            return "你们都对相同的活动感兴趣"
        else:
            return "你们互相匹配成功"
    
    def get_user_match_actions(self, user_id: str, match_type: str = None, 
                              page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        获取用户的匹配操作历史
        
        Args:
            user_id: 用户ID
            match_type: 匹配类型筛选
            page: 页码
            page_size: 每页数量
            
        Returns:
            操作历史数据
        """
        query = self.db.query(MatchAction).filter(MatchAction.user_id == user_id)
        
        if match_type:
            query = query.filter(MatchAction.match_type == match_type)
        
        query = query.order_by(MatchAction.created_at.desc())
        
        total = query.count()
        actions = query.offset((page - 1) * page_size).limit(page_size).all()
        
        action_list = []
        for action in actions:
            target_user = self.db.query(User).filter(User.id == action.target_user_id).first()
            action_list.append({
                "id": action.id,
                "targetUser": {
                    "id": target_user.id if target_user else None,
                    "name": target_user.nick_name if target_user else "未知用户"
                },
                "actionType": action.action_type.value,
                "matchType": action.match_type,
                "createdAt": action.created_at.isoformat()
            })
        
        return {
            "actions": action_list,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total
            }
        }