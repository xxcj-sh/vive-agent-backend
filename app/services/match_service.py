from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from app.models.match_action import MatchAction, MatchResult, MatchActionType, MatchResultStatus
from app.models.user import User
from datetime import datetime, timedelta
import uuid
import json

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
            source = action_data.get("source", "user")  # 新增：操作来源
            metadata = action_data.get("metadata", {})  # 新增：元数据
            
            if not all([card_id, action_type, match_type]):
                raise ValueError("缺少必要参数: cardId, action, matchType")
            
            # 确保参数类型正确
            card_id = str(card_id)
            action_type = str(action_type)
            match_type = str(match_type)
            
            # 验证操作类型
            if action_type not in [t.value for t in MatchActionType]:
                raise ValueError(f"无效的操作类型: {action_type}")
            
            # 解析目标用户ID
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
                    "existingAction": existing_action.action_type.value,
                    "actionId": str(existing_action.id)
                }
            
            # 创建匹配操作记录
            match_action = MatchAction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                target_user_id=target_user_id,
                target_card_id=card_id,
                action_type=MatchActionType(action_type),
                match_type=match_type,
                scene_context=action_data.get("sceneContext"),
                source=source,
                metadata=json.dumps(metadata) if metadata else None
            )
            
            self.db.add(match_action)
            self.db.commit()
            self.db.refresh(match_action)
            
            # 处理匹配逻辑
            is_match, match_id = self._process_match_logic(
                user_id, target_user_id, card_id, match_type, str(match_action.id), action_type
            )
            
            return {
                "isMatch": is_match,
                "matchId": match_id,
                "actionId": str(match_action.id),
                "message": "操作成功",
                "source": source
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"提交匹配操作失败: {str(e)}")
    
    def _process_match_logic(self, user_id: str, target_user_id: str, 
                           card_id: str, match_type: str, current_action_id: str, action_type: str) -> tuple[bool, Optional[str]]:
        """
        处理匹配逻辑
        
        Args:
            user_id: 当前用户ID
            target_user_id: 目标用户ID
            card_id: 卡片ID
            match_type: 匹配类型
            current_action_id: 当前操作ID
            action_type: 操作类型
            
        Returns:
            (是否匹配, 匹配ID)
        """
        # AI推荐操作不触发匹配检查
        if action_type in ["ai_recommend_after_user_chat", "ai_recommend_by_system"]:
            return False, None
        
        # 只有喜欢或超级喜欢才检查双向匹配
        if action_type not in ["like", "super_like"]:
            return False, None
        
        return self._check_mutual_match(
            user_id, target_user_id, card_id, match_type, current_action_id
        )
    
    def get_ai_recommendations(self, user_id: str, scene_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取AI推荐记录
        
        Args:
            user_id: 用户ID
            scene_type: 场景类型
            limit: 返回数量限制
            
        Returns:
            AI推荐列表
        """
        try:
            recommendations = self.db.query(MatchAction).filter(
                MatchAction.user_id == user_id,
                MatchAction.action_type.in_([
                    MatchActionType.AI_RECOMMEND_AFTER_USER_CHAT,
                    MatchActionType.AI_RECOMMEND_BY_SYSTEM
                ]),
                MatchAction.match_type == scene_type,
                MatchAction.is_processed == False
            ).order_by(MatchAction.created_at.desc()).limit(limit).all()
            
            result = []
            for rec in recommendations:
                target_user = self.db.query(User).filter(User.id == rec.target_user_id).first()
                if target_user:
                    metadata = {}
                    if rec.metadata:
                        try:
                            metadata = json.loads(rec.metadata)
                        except:
                            pass
                    
                    result.append({
                        "id": str(rec.id),
                        "targetUserId": str(rec.target_user_id),
                        "targetCardId": str(rec.target_card_id),
                        "actionType": rec.action_type.value,
                        "sceneContext": rec.scene_context,
                        "metadata": metadata,
                        "createdAt": rec.created_at.isoformat(),
                        "targetUser": {
                            "id": str(target_user.id),
                            "name": getattr(target_user, 'nick_name', None) or getattr(target_user, 'name', '匿名用户'),
                            "avatar": getattr(target_user, 'avatar_url', None)
                        }
                    })
            
            return result
            
        except Exception as e:
            print(f"获取AI推荐失败: {str(e)}")
            return []
    
    def update_ai_recommendation_status(self, action_id: str, is_processed: bool = True) -> bool:
        """
        更新AI推荐处理状态
        
        Args:
            action_id: 操作ID
            is_processed: 是否已处理
            
        Returns:
            是否更新成功
        """
        try:
            action = self.db.query(MatchAction).filter(MatchAction.id == action_id).first()
            if action:
                action.is_processed = is_processed
                if is_processed:
                    action.processed_at = datetime.utcnow()
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            print(f"更新AI推荐状态失败: {str(e)}")
            return False
    
    def get_unprocessed_ai_recommendations(self, limit: int = 100) -> List[MatchAction]:
        """
        获取未处理的AI推荐
        
        Args:
            limit: 返回数量限制
            
        Returns:
            未处理的AI推荐列表
        """
        return self.db.query(MatchAction).filter(
            MatchAction.action_type.in_([
                MatchActionType.AI_RECOMMEND_AFTER_USER_CHAT,
                MatchActionType.AI_RECOMMEND_BY_SYSTEM
            ]),
            MatchAction.is_processed == False
        ).order_by(MatchAction.created_at.asc()).limit(limit).all()
    
    def get_match_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        获取用户匹配统计
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            统计信息
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 基础统计
            total_actions = self.db.query(MatchAction).filter(
                MatchAction.user_id == user_id,
                MatchAction.created_at >= cutoff_date
            ).count()
            
            action_stats = self.db.query(
                MatchAction.action_type,
                func.count(MatchAction.id).label('count')
            ).filter(
                MatchAction.user_id == user_id,
                MatchAction.created_at >= cutoff_date
            ).group_by(MatchAction.action_type).all()
            
            stats = {action_type.value: 0 for action_type in MatchActionType}
            for action_type, count in action_stats:
                if action_type:
                    stats[action_type.value] = count
            
            # AI推荐统计
            ai_recommendations = self.db.query(MatchAction).filter(
                MatchAction.user_id == user_id,
                MatchAction.action_type.in_([
                    MatchActionType.AI_RECOMMEND_AFTER_USER_CHAT,
                    MatchActionType.AI_RECOMMEND_BY_SYSTEM
                ]),
                MatchAction.created_at >= cutoff_date
            ).count()
            
            return {
                "totalActions": total_actions,
                "actionBreakdown": stats,
                "aiRecommendations": ai_recommendations,
                "period": f"{days} days"
            }
            
        except Exception as e:
            print(f"获取匹配统计失败: {str(e)}")
            return {}
    
    def _extract_target_user_id(self, card_id: str, match_type: str) -> Optional[str]:
        """从卡片ID中提取目标用户ID - 保持原有实现"""
        # ... existing code ...
        
    def _check_mutual_match(self, user_id: str, target_user_id: str, 
                           card_id: str, match_type: str, current_action_id: str) -> tuple[bool, Optional[str]]:
        """检查双向匹配 - 保持原有实现，添加过期时间处理"""
        # ... existing code ...
        
    def get_recommendation_cards(self, user_id: str, scene_type: str, 
                               user_role: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        获取匹配推荐卡片
        
        Args:
            user_id: 用户ID
            scene_type: 场景类型 (housing, dating, activity)
            user_role: 用户角色 (seeker, provider, participant, organizer)
            page: 页码
            page_size: 每页数量
            
        Returns:
            包含卡片列表和分页信息的字典
        """
        try:
            from app.services.match_card_strategy import match_card_strategy
            from app.models.user import User
            
            # 获取当前用户信息
            current_user = self.db.query(User).filter(User.id == user_id).first()
            if not current_user:
                return {"cards": [], "total": 0}
            
            # 构建当前用户信息字典
            current_user_dict = {
                "id": str(current_user.id),
                "nickName": getattr(current_user, 'nick_name', None) or getattr(current_user, 'name', '匿名用户'),
                "gender": getattr(current_user, 'gender', 0),
                "age": getattr(current_user, 'age', 25),
                "occupation": getattr(current_user, 'occupation', ''),
                "location": getattr(current_user, 'location', ''),
                "bio": getattr(current_user, 'bio', ''),
                "interests": getattr(current_user, 'interests', []),
                "avatarUrl": getattr(current_user, 'avatar_url', None),
                "preferences": getattr(current_user, 'preferences', {})
            }
            
            # 使用匹配卡片策略获取推荐卡片
            result = match_card_strategy.get_match_cards(
                match_type=scene_type,
                user_role=user_role,
                page=page,
                page_size=page_size,
                current_user=current_user_dict
            )
            
            # 转换返回格式
            cards = result.get("list", [])
            total = result.get("total", 0)
            
            # 格式化卡片数据
            formatted_cards = []
            for card in cards:
                formatted_card = {
                    "id": card.get("id"),
                    "userId": card.get("userId"),
                    "name": card.get("name", "匿名用户"),
                    "avatar": card.get("avatar"),
                    "age": card.get("age", 25),
                    "occupation": card.get("occupation", ""),
                    "location": card.get("location", ""),
                    "bio": card.get("bio", ""),
                    "interests": card.get("interests", []),
                    "sceneType": scene_type,
                    "userRole": card.get("userRole", user_role),
                    "createdAt": card.get("createdAt", ""),
                    "matchScore": card.get("matchScore", 75)
                }
                
                # 根据场景类型添加特定字段
                if scene_type == "housing":
                    if user_role == "seeker":
                        # 租客看房源
                        formatted_card.update({
                            "houseTitle": card.get("houseTitle", ""),
                            "housePrice": card.get("housePrice", 0),
                            "houseArea": card.get("houseArea", 0),
                            "houseLocation": card.get("houseLocation", ""),
                            "houseImages": card.get("houseImages", []),
                            "landlordName": card.get("landlordName", "")
                        })
                    else:
                        # 房东看租客需求
                        formatted_card.update({
                            "budget": card.get("budget", 0),
                            "leaseDuration": card.get("leaseDuration", ""),
                            "moveInDate": card.get("moveInDate", ""),
                            "tenantRequirements": card.get("tenantRequirements", [])
                        })
                        
                elif scene_type == "dating":
                    formatted_card.update({
                        "gender": card.get("gender", 0),
                        "education": card.get("education", ""),
                        "height": card.get("height", 0),
                        "relationshipStatus": card.get("relationshipStatus", "")
                    })
                    
                elif scene_type == "activity":
                    if user_role == "seeker":
                        # 参与者看活动
                        formatted_card.update({
                            "activityName": card.get("activityName", ""),
                            "activityType": card.get("activityType", ""),
                            "activityPrice": card.get("activityPrice", 0),
                            "activityTime": card.get("activityTime", ""),
                            "activityLocation": card.get("activityLocation", ""),
                            "organizerName": card.get("organizerName", "")
                        })
                    else:
                        # 组织者看参与者
                        formatted_card.update({
                            "preferredActivity": card.get("preferredActivity", ""),
                            "budgetRange": card.get("budgetRange", ""),
                            "availability": card.get("availability", "")
                        })
                
                formatted_cards.append(formatted_card)
            
            return {
                "cards": formatted_cards,
                "total": total
            }
            
        except Exception as e:
            print(f"获取匹配推荐卡片失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"cards": [], "total": 0}

    def get_user_matches(self, user_id: str, status: str = "all", 
                        page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        获取用户匹配列表
        
        Args:
            user_id: 用户ID
            status: 匹配状态 (all, pending, matched, rejected, expired)
            page: 页码
            page_size: 每页数量
            
        Returns:
            包含匹配列表和分页信息的字典
        """
        try:
            from sqlalchemy import and_, or_
            from app.models.match_action import MatchAction, MatchActionType
            from app.models.user import User
            
            # 基础查询：获取用户的所有匹配操作
            query = self.db.query(MatchAction).filter(
                MatchAction.user_id == user_id
            )
            
            # 根据状态筛选
            if status != "all":
                if status == "pending":
                    # 待处理：用户发起的操作，等待对方回应
                    query = query.filter(
                        MatchAction.action_type.in_([
                            MatchActionType.LIKE,
                            MatchActionType.SUPER_LIKE
                        ])
                    )
                elif status == "matched":
                    # 已匹配：双向匹配成功
                    query = query.filter(
                        MatchAction.action_type == MatchActionType.MUTUAL_MATCH
                    )
                elif status == "rejected":
                    # 已拒绝：用户或对方拒绝
                    query = query.filter(
                        MatchAction.action_type == MatchActionType.REJECT
                    )
                elif status == "expired":
                    # 已过期：超过有效期的操作
                    cutoff_date = datetime.utcnow() - timedelta(days=7)
                    query = query.filter(
                        MatchAction.created_at < cutoff_date,
                        MatchAction.action_type.in_([
                            MatchActionType.LIKE,
                            MatchActionType.SUPER_LIKE
                        ])
                    )
            
            # 获取总数
            total = query.count()
            
            # 获取分页数据
            matches = query.order_by(MatchAction.created_at.desc()).offset(
                (page - 1) * page_size
            ).limit(page_size).all()
            
            # 格式化匹配数据
            formatted_matches = []
            for match in matches:
                # 获取目标用户信息
                target_user = self.db.query(User).filter(
                    User.id == match.target_user_id
                ).first()
                
                if not target_user:
                    continue
                
                # 获取对应的卡片信息
                from app.models.user_card_db import UserCard
                target_card = self.db.query(UserCard).filter(
                    UserCard.user_id == match.target_user_id,
                    UserCard.scene_type == match.match_type,
                    UserCard.is_active == 1
                ).first()
                
                match_data = {
                    "id": str(match.id),
                    "targetUserId": str(target_user.id),
                    "targetUserName": getattr(target_user, 'nick_name', None) or getattr(target_user, 'name', '匿名用户'),
                    "targetUserAvatar": getattr(target_user, 'avatar_url', None),
                    "matchType": match.match_type,
                    "actionType": match.action_type.value,
                    "status": self._get_match_status(match.action_type),
                    "createdAt": match.created_at.isoformat() if match.created_at else "",
                    "updatedAt": match.updated_at.isoformat() if match.updated_at else ""
                }
                
                # 添加场景特定信息
                if match.match_type == "housing":
                    if target_card:
                        match_data.update({
                            "houseTitle": getattr(target_card, 'title', ''),
                            "housePrice": getattr(target_card, 'price', 0),
                            "houseLocation": getattr(target_card, 'location', '')
                        })
                elif match.match_type == "activity":
                    if target_card:
                        match_data.update({
                            "activityName": getattr(target_card, 'title', ''),
                            "activityTime": getattr(target_card, 'activity_time', ''),
                            "activityLocation": getattr(target_card, 'location', '')
                        })
                elif match.match_type == "dating":
                    match_data.update({
                        "targetUserAge": getattr(target_user, 'age', 25),
                        "targetUserGender": getattr(target_user, 'gender', 0)
                    })
                
                formatted_matches.append(match_data)
            
            return {
                "matches": formatted_matches,
                "total": total
            }
            
        except Exception as e:
            print(f"获取用户匹配列表失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"matches": [], "total": 0}
    
    def _get_match_status(self, action_type: MatchActionType) -> str:
        """根据操作类型获取匹配状态"""
        status_mapping = {
            MatchActionType.LIKE: "pending",
            MatchActionType.SUPER_LIKE: "pending",
            MatchActionType.REJECT: "rejected",
            MatchActionType.MUTUAL_MATCH: "matched"
        }
        return status_mapping.get(action_type, "unknown")