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
        
    def get_user_matches(self, user_id: str, status: str = "all", 
                        page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """获取用户匹配列表 - 保持原有实现"""
        # ... existing code ...