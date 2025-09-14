"""
匹配卡片策略服务
负责控制返回匹配卡片的策略和逻辑
"""

from typing import Dict, List, Any, Optional
from enum import Enum

from app.services.data_adapter import DataService

# 创建数据服务实例
data_service = DataService()
from app.services.media_service import media_service
from app.models.user import User
from app.models.user_card_db import UserCard
from app.models.enums import UserRole, MatchType, Gender
from sqlalchemy.orm import Session
from app.database import get_db


class MatchStrategy(Enum):
    """匹配策略枚举"""
    RANDOM = "random"           # 随机推荐
    PREFERENCE = "preference"   # 基于偏好
    LOCATION = "location"       # 基于位置
    ACTIVITY = "activity"       # 基于活动
    COMPATIBILITY = "compatibility"  # 基于兼容性


class MatchCardStrategy:
    """匹配卡片策略控制器"""
    
    def __init__(self):
        self.strategy_weights = {
            MatchStrategy.RANDOM: 0.2,
            MatchStrategy.PREFERENCE: 0.3,
            MatchStrategy.LOCATION: 0.2,
            MatchStrategy.ACTIVITY: 0.15,
            MatchStrategy.COMPATIBILITY: 0.15
        }
    
    def get_match_cards(
        self, 
        match_type: str, 
        user_role: str, 
        page: int, 
        page_size: int,
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        获取匹配卡片的主要入口方法
        
        Args:
            match_type: 匹配类型 (housing, dating, activity等)
            user_role: 用户角色 (seeker, provider等)
            page: 页码
            page_size: 每页数量
            current_user: 当前用户信息
            
        Returns:
            包含卡片列表和分页信息的字典
        """
        try:
            print(f"MatchCardStrategy.get_match_cards - 参数: match_type={match_type}, user_role={user_role}, page={page}, page_size={page_size}")
            if current_user:
                print(f"MatchCardStrategy: 当前用户ID={current_user.get('id')}, nickName={current_user.get('nickName')}")
            else:
                print("MatchCardStrategy: 无当前用户信息")
                
            # 根据匹配类型选择不同的策略
            if match_type == "housing":
                print("MatchCardStrategy: 选择房源匹配策略")
                result = self._get_housing_cards(user_role, page, page_size, current_user)
            elif match_type == "dating":
                print("MatchCardStrategy: 选择交友匹配策略")
                result = self._get_dating_cards(user_role, page, page_size, current_user)
            elif match_type == "activity":
                print("MatchCardStrategy: 选择活动匹配策略")
                result = self._get_activity_cards(user_role, page, page_size, current_user)
            else:
                print(f"MatchCardStrategy: 选择默认策略 match_type={match_type}")
                result = self._get_default_cards(match_type, user_role, page, page_size, current_user)
            
            print(f"MatchCardStrategy: 返回结果 - 总数={result.get('total', 0)}, 列表长度={len(result.get('list', []))}, 策略={result.get('strategy', 'unknown')}")
            return result
                
        except Exception as e:
            print(f"匹配卡片策略执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 降级到基础数据服务
            return data_service.get_cards(match_type, user_role, page, page_size)
    
    def _get_housing_cards(
        self, 
        user_role: str, 
        page: int, 
        page_size: int, 
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取房源匹配卡片"""
        
        # 根据用户角色决定返回什么类型的卡片
        if user_role == "seeker":
            # 租客看到的是房东的房源信息
            return self._get_housing_cards_for_seeker(page, page_size, current_user)
        elif user_role == "provider":
            # 房东看到的是租客的需求信息
            return self._get_tenant_cards_for_provider(page, page_size, current_user)
        else:
            # 默认返回房源卡片
            return self._get_housing_cards_for_seeker(page, page_size, current_user)
    
    def _get_dating_cards(
        self, 
        user_role: str, 
        page: int, 
        page_size: int, 
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取交友匹配卡片"""
        
        # 交友场景：显示其他用户的个人信息
        return self._get_dating_cards_from_db(page, page_size, current_user)
    
    def _get_activity_cards(
        self, 
        user_role: str, 
        page: int, 
        page_size: int, 
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取活动匹配卡片"""
        
        # 根据用户角色决定返回什么类型的卡片
        if user_role == "seeker":
            # 参与者看到的是组织者的活动信息
            return self._get_activity_cards_for_seeker(page, page_size, current_user)
        elif user_role == "provider":
            # 组织者看到的是参与者的信息
            return self._get_participant_cards_for_organizer(page, page_size, current_user)
        else:
            # 默认返回活动卡片
            return self._get_activity_cards_for_seeker(page, page_size, current_user)
    
    def _get_default_cards(
        self, 
        match_type: str, 
        user_role: str, 
        page: int, 
        page_size: int, 
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """默认卡片获取策略"""
        return data_service.get_cards(match_type, user_role, page, page_size)
    
    def _get_housing_cards_for_seeker(self, page: int, page_size: int, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从数据库获取租客视角的房源卡片（显示房东的房源信息）"""
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 查询房东用户（提供房源的用户）
            landlords_query = db.query(User).join(UserCard).filter(
                UserCard.role_type == 'housing_provider',
                UserCard.scene_type == 'housing',
                UserCard.visibility == 'public'
            )
            
            # 排除当前用户
            if current_user and current_user.get('id'):
                landlords_query = landlords_query.filter(User.id != current_user['id'])
            
            # 分页查询
            offset = (page - 1) * page_size
            landlords = landlords_query.offset(offset).limit(page_size).all()
            total_count = landlords_query.count()
            
            # 转换为卡片数据
            cards = []
            for landlord in landlords:
                card_data = self._convert_user_to_housing_card_for_seeker(landlord)
                # 添加多媒体数据
                card_data = self._enrich_card_with_media(card_data, str(landlord.id))
                cards.append(card_data)
            
            return {
                "total": total_count,
                "list": cards,
                "page": page,
                "pageSize": page_size,
                "strategy": "housing_seeker_view_db"
            }
            
        except Exception as e:
            print(f"数据库查询失败: {str(e)}")
            # 返回空数据而不是样本数据
            return {
                "total": 0,
                "list": [],
                "page": page,
                "pageSize": page_size,
                "strategy": "housing_seeker_view_db_error"
            }
    
    def _get_tenant_cards_for_provider(self, page: int, page_size: int, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从数据库获取房东视角的租客卡片（显示租客的需求信息）"""
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 查询租客用户（寻找房源的用户）
            tenants_query = db.query(User).join(UserCard).filter(
                UserCard.role_type == 'housing_seeker',
                UserCard.scene_type == 'housing',
                UserCard.visibility == 'public'
            )
            
            # 排除当前用户
            if current_user and current_user.get('id'):
                tenants_query = tenants_query.filter(User.id != current_user['id'])
            
            # 分页查询
            offset = (page - 1) * page_size
            tenants = tenants_query.offset(offset).limit(page_size).all()
            total_count = tenants_query.count()
            
            # 转换为卡片数据
            cards = []
            for tenant in tenants:
                card_data = self._convert_user_to_tenant_card_for_provider(tenant)
                # 添加多媒体数据
                card_data = self._enrich_card_with_media(card_data, str(tenant.id))
                cards.append(card_data)
            
            return {
                "total": total_count,
                "list": cards,
                "page": page,
                "pageSize": page_size,
                "strategy": "housing_provider_view_db"
            }
            
        except Exception as e:
            print(f"数据库查询失败: {str(e)}")
            # 返回空数据而不是样本数据
            return {
                "total": 0,
                "list": [],
                "page": page,
                "pageSize": page_size,
                "strategy": "housing_provider_view_db_error"
            }
    

    

    
    def _get_dating_cards_from_db(self, page: int, page_size: int, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从数据库获取交友卡片"""
        try:
            print(f"_get_dating_cards_from_db: 开始查询交友卡片, page={page}, page_size={page_size}")
            
            # 获取数据库会话
            db = next(get_db())
            
            # 查询交友卡片
            dating_query = db.query(User).join(UserCard).filter(
                UserCard.scene_type == 'dating',
                UserCard.visibility == 'public'
            )
            
            print(f"_get_dating_cards_from_db: 基础查询条件 - UserCard.scene_type='dating', visibility='public'")
            
            # 排除当前用户
            if current_user and current_user.get('id'):
                dating_query = dating_query.filter(User.id != current_user['id'])
                print(f"_get_dating_cards_from_db: 排除当前用户 user_id={current_user.get('id')}")
            
            # 打印查询SQL
            print(f"_get_dating_cards_from_db: 查询SQL: {str(dating_query.statement)}")
            
            # 分页查询
            offset = (page - 1) * page_size
            dating_users = dating_query.offset(offset).limit(page_size).all()
            total_count = dating_query.count()
            
            print(f"_get_dating_cards_from_db: 查询结果 - 总数={total_count}, 当前页数量={len(dating_users)}")
            
            # 转换为卡片数据
            cards = []
            for i, user in enumerate(dating_users):
                print(f"_get_dating_cards_from_db: 处理第{i+1}个用户 user_id={user.id}")
                card_data = self._convert_user_to_dating_card(user)
                # 添加多媒体数据
                card_data = self._enrich_card_with_media(card_data, str(user.id))
                cards.append(card_data)
            
            return {
                "total": total_count,
                "list": cards,
                "page": page,
                "pageSize": page_size,
                "strategy": "dating_db_query"
            }
            
        except Exception as e:
            print(f"数据库查询失败: {str(e)}")
            # 返回空数据而不是样本数据
            return {
                "total": 0,
                "list": [],
                "page": page,
                "pageSize": page_size,
                "strategy": "dating_db_query_error"
            }
    
    def _get_activity_cards_for_seeker(self, page: int, page_size: int, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从数据库获取活动参与者视角的活动卡片（显示活动组织者信息）"""
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 查询活动组织者
            organizers_query = db.query(User).join(UserCard).filter(
                UserCard.role_type == 'activity_organizer',
                UserCard.scene_type == 'activity',
                UserCard.visibility == 'public'
            )
            
            # 排除当前用户
            if current_user and current_user.get('id'):
                organizers_query = organizers_query.filter(User.id != current_user['id'])
            
            # 分页查询
            offset = (page - 1) * page_size
            organizers = organizers_query.offset(offset).limit(page_size).all()
            total_count = organizers_query.count()
            
            # 转换为卡片数据
            cards = []
            for organizer in organizers:
                card_data = self._convert_user_to_activity_card_for_seeker(organizer)
                # 添加多媒体数据
                card_data = self._enrich_card_with_media(card_data, str(organizer.id))
                cards.append(card_data)
            
            return {
                "total": total_count,
                "list": cards,
                "page": page,
                "pageSize": page_size,
                "strategy": "activity_seeker_view_db"
            }
            
        except Exception as e:
            print(f"数据库查询失败: {str(e)}")
            # 返回空数据而不是样本数据
            return {
                "total": 0,
                "list": [],
                "page": page,
                "pageSize": page_size,
                "strategy": "activity_seeker_view_db_error"
            }
    
    def _get_participant_cards_for_organizer(self, page: int, page_size: int, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从数据库获取组织者视角的参与者卡片"""
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 查询活动参与者
            participants_query = db.query(User).join(UserCard).filter(
                UserCard.role_type == 'activity_participant',
                UserCard.scene_type == 'activity',
                UserCard.visibility == 'public'
            )
            
            # 排除当前用户
            if current_user and current_user.get('id'):
                participants_query = participants_query.filter(User.id != current_user['id'])
            
            # 分页查询
            offset = (page - 1) * page_size
            participants = participants_query.offset(offset).limit(page_size).all()
            total_count = participants_query.count()
            
            # 转换为卡片数据
            cards = []
            for participant in participants:
                card_data = self._convert_user_to_participant_card_for_organizer(participant)
                # 添加多媒体数据
                card_data = self._enrich_card_with_media(card_data, str(participant.id))
                cards.append(card_data)
            
            return {
                "total": total_count,
                "list": cards,
                "page": page,
                "pageSize": page_size,
                "strategy": "activity_organizer_view_db"
            }
            
        except Exception as e:
            print(f"数据库查询失败: {str(e)}")
            # 返回空数据而不是样本数据
            return {
                "total": 0,
                "list": [],
                "page": page,
                "pageSize": page_size,
                "strategy": "activity_organizer_view_db_error"
            }
    

    

    

    

    
    def _convert_user_to_housing_card_for_seeker(self, landlord: User) -> Dict[str, Any]:
        """将房东用户数据转换为租客视角的房源卡片"""
        # 获取用户的房源卡片信息
        from sqlalchemy.orm import Session
        from app.database import get_db
        from app.models.user_card_db import UserCard
        
        db = next(get_db())
        user_card = db.query(UserCard).filter(
            UserCard.user_id == str(landlord.id),
            UserCard.scene_type == 'housing',
            UserCard.role_type == 'housing_provider',
            UserCard.is_active == 1,
            UserCard.is_deleted == 0
        ).first()
        
        card_data = user_card.profile_data if user_card and user_card.profile_data else {}
        
        return {
            "id": f"housing_db_{landlord.id}",
            "matchType": "housing",
            "userRole": "seeker",
            # 房源基本信息
            "houseImage": "",  # 将通过多媒体服务填充
            "houseInfo": {
                "price": card_data.get('price', 5000),
                "area": card_data.get('area', 80),
                "orientation": card_data.get('orientation', '南北通透'),
                "hasElevator": card_data.get('hasElevator', True),
                "location": card_data.get('location', '朝阳区'),
                "community": card_data.get('community', '未知小区'),
                "images": [],  # 将通过多媒体服务填充
                "videoUrl": ""  # 将通过多媒体服务填充
            },
            # 房东信息
            "landlordInfo": {
                "avatar": "",  # 将通过多媒体服务填充
                "name": landlord.nick_name or landlord.name or f"用户{landlord.id}",
                "age": card_data.get('age', 30),
                "user_id": landlord.id
            },
            # 详情页面需要的额外信息
            "area": card_data.get('area', 80),
            "orientation": card_data.get('orientation', '南北通透'),
            "floor": card_data.get('floor', '10/20层'),
            "hasElevator": card_data.get('hasElevator', True),
            "decoration": card_data.get('decoration', '精装修'),
            "price": card_data.get('price', 5000),
            "deposit": card_data.get('deposit', '押一付一'),
            "community": card_data.get('community', '未知小区'),
            "location": card_data.get('location', '朝阳区'),
            "title": f"{card_data.get('type', '两')}居室 - {card_data.get('community', '未知小区')}",
            "publishTime": int(landlord.created_at.timestamp()) if landlord.created_at else 0,
            "recommendReason": "位置便利，交通方便"
        }
    
    def _convert_user_to_tenant_card_for_provider(self, tenant: User) -> Dict[str, Any]:
        """将租客用户数据转换为房东视角的租客卡片"""
        from sqlalchemy.orm import Session
        from app.models.user_card_db import UserCard as UserCardModel
        
        # 获取用户的卡片数据
        db = next(get_db())
        card = db.query(UserCardModel).filter(
            UserCardModel.user_id == tenant.id,
            UserCardModel.scene_type == 'housing',
            UserCardModel.role_type == 'housing_seeker'
        ).first()
        
        card_data = card.profile_data if card and card.profile_data else {}
        
        return {
            "id": f"tenant_db_{tenant.id}",
            "matchType": "housing",
            "userRole": "provider",
            # 租客基本信息
            "name": tenant.nick_name or tenant.username or f"用户{tenant.id}",
            "age": card_data.get('age', 25),
            "occupation": card_data.get('occupation', '未知职业'),
            "avatar": "",  # 将通过多媒体服务填充
            "videoUrl": "",  # 将通过多媒体服务填充
            "images": [],  # 将通过多媒体服务填充
            # 租房需求信息
            "tenantInfo": {
                "budget": card_data.get('housing_budget', 5000),
                "leaseDuration": card_data.get('housing_lease_duration', '一年'),
                "moveInDate": card_data.get('housing_move_in_date', '随时'),
                "priceRange": f"{card_data.get('housing_budget_min', 3000)}-{card_data.get('housing_budget_max', 8000)}元",
                "leaseTerm": card_data.get('housing_lease_duration', '一年')
            },
            # 详情页面信息
            "location": [card_data.get('city', '北京市'), card_data.get('district', '朝阳区')],
            "bio": card_data.get('bio', '工作稳定，寻找合适的住所'),
            "interests": card_data.get('interests', '').split(',') if card_data.get('interests', '') else [],
            "priceRange": f"{card_data.get('housing_budget_min', 3000)}-{card_data.get('housing_budget_max', 8000)}元",
            "leaseTerm": card_data.get('housing_lease_duration', '一年'),
            "moveInDate": card_data.get('housing_move_in_date', '随时入住'),
            "recommendReason": "工作稳定，信誉良好"
        }
    
    def _convert_user_to_dating_card(self, user: User) -> Dict[str, Any]:
        """将用户数据转换为交友卡片"""
        from sqlalchemy.orm import Session
        from app.models.user_card_db import UserCard as UserCardModel
        
        # 获取用户的卡片数据
        db = next(get_db())
        card = db.query(UserCardModel).filter(
            UserCardModel.user_id == user.id,
            UserCardModel.scene_type == 'dating'
        ).first()
        
        card_data = card.profile_data if card and card.profile_data else {}
        
        return {
            "id": f"dating_db_{user.id}",
            "matchType": "dating",
            "userRole": "user",
            "name": user.nick_name or user.username or f"用户{user.id}",
            "nickName": user.nick_name or user.username,
            "age": card_data.get('age', 25),
            "gender": card_data.get('gender', 1),
            "occupation": card_data.get('occupation', '未知职业'),
            "location": [card_data.get('city', '北京市'), card_data.get('district', '朝阳区')],
            "bio": card_data.get('bio', '热爱生活，寻找志同道合的朋友'),
            "interests": card_data.get('interests', '').split(',') if card_data.get('interests', '') else [],
            "hobbies": card_data.get('hobbies', '').split(',') if card_data.get('hobbies', '') else [],
            # 多媒体数据（将通过多媒体服务填充）
            "avatar": "",
            "avatarUrl": "",
            "videoUrl": "",
            "images": [],
            # 交友特定信息
            "education": card_data.get('education', '本科'),
            "height": card_data.get('height', 170),
            "income": card_data.get('income_range', '10-20万'),
            "lookingFor": card_data.get('looking_for', '寻找志同道合的朋友'),
            "recommendReason": "兴趣爱好相似"
        }
    
    def _convert_user_to_activity_card_for_seeker(self, organizer: User) -> Dict[str, Any]:
        """将组织者用户数据转换为参与者视角的活动卡片"""
        from sqlalchemy.orm import Session
        from app.models.user_card_db import UserCard as UserCardModel
        
        # 获取用户的卡片数据
        db = next(get_db())
        card = db.query(UserCardModel).filter(
            UserCardModel.user_id == organizer.id,
            UserCardModel.scene_type == 'activity',
            UserCardModel.role_type == 'activity_organizer'
        ).first()
        
        card_data = card.profile_data if card and card.profile_data else {}
        
        return {
            "id": f"activity_db_{organizer.id}",
            "matchType": "activity",
            "userRole": "seeker",
            "name": organizer.nick_name or organizer.username or f"组织者{organizer.id}",
            "age": card_data.get('age', 30),
            "occupation": card_data.get('occupation', '活动策划师'),
            # 多媒体数据（将通过多媒体服务填充）
            "avatar": "",
            "videoUrl": "",
            "images": [],
            # 活动信息
            "activityName": card_data.get('activity_name', '周末户外活动'),
            "activityType": card_data.get('activity_type', '户外运动'),
            "activityTime": card_data.get('activity_time', '周末上午 9:00-12:00'),
            "activityLocation": card_data.get('activity_location', '朝阳公园'),
            "activityPrice": card_data.get('activity_price', 100),
            "activityDuration": card_data.get('activity_duration', '3小时'),
            "activityMaxParticipants": card_data.get('activity_max_participants', 20),
            "activityDifficulty": card_data.get('activity_difficulty', '初级'),
            "activityIncludes": card_data.get('activity_includes', '专业指导,活动用品').split(','),
            "activityDescription": card_data.get('activity_description', '欢迎参加我们的活动，一起度过愉快的时光'),
            "recommendReason": "符合您的兴趣偏好"
        }
    
    def _convert_user_to_participant_card_for_organizer(self, participant: User) -> Dict[str, Any]:
        """将参与者用户数据转换为组织者视角的参与者卡片"""
        from sqlalchemy.orm import Session
        from app.models.user_card_db import UserCard as UserCardModel
        
        # 获取用户的卡片数据
        db = next(get_db())
        card = db.query(UserCardModel).filter(
            UserCardModel.user_id == participant.id,
            UserCardModel.scene_type == 'activity',
            UserCardModel.role_type == 'activity_participant'
        ).first()
        
        card_data = card.profile_data if card and card.profile_data else {}
        
        return {
            "id": f"participant_db_{participant.id}",
            "matchType": "activity",
            "userRole": "provider",
            # 参与者基本信息
            "name": participant.nick_name or participant.username or f"用户{participant.id}",
            "age": card_data.get('age', 25),
            "occupation": card_data.get('occupation', '未知职业'),
            "avatar": "",  # 将通过多媒体服务填充
            "videoUrl": "",  # 将通过多媒体服务填充
            "images": [],  # 将通过多媒体服务填充
            # 活动偏好信息
            "preferredActivity": card_data.get('preferred_activity_type', '户外运动'),
            "budgetRange": f"{card_data.get('activity_budget_min', 50)}-{card_data.get('activity_budget_max', 200)}元",
            "preferredTime": card_data.get('preferred_activity_time', '周末上午'),
            "preferredLocation": card_data.get('preferred_activity_location', '朝阳区'),
            # 详情页面信息
            "location": [card_data.get('city', '北京市'), card_data.get('district', '朝阳区')],
            "bio": card_data.get('bio', '热爱运动，希望通过活动结识朋友'),
            "interests": card_data.get('interests', '').split(',') if card_data.get('interests', '') else [],
            "recommendReason": "活动参与积极，兴趣匹配"
        }
    
    def _enrich_card_with_media(self, card_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """为卡片数据添加多媒体信息"""
        try:
            # 获取用户的多媒体数据
            media_data = media_service.get_user_media(user_id)
            
            # 添加头像
            if media_data.get('avatar_url'):
                card_data['avatar'] = media_data['avatar_url']
                card_data['avatarUrl'] = media_data['avatar_url']
                
                # 为房源卡片添加房东头像
                if 'landlordInfo' in card_data:
                    card_data['landlordInfo']['avatar'] = media_data['avatar_url']
            
            # 添加视频
            if media_data.get('video_url'):
                card_data['videoUrl'] = media_data['video_url']
                
                # 为房源卡片添加房源视频
                if 'houseInfo' in card_data:
                    card_data['houseInfo']['videoUrl'] = media_data['video_url']
            
            # 添加图片集
            if media_data.get('images'):
                card_data['images'] = media_data['images']
                
                # 为房源卡片添加房源图片
                if 'houseInfo' in card_data:
                    card_data['houseInfo']['images'] = media_data['images']
                    if media_data['images']:
                        card_data['houseImage'] = media_data['images'][0]
            
        except Exception as e:
            print(f"获取用户 {user_id} 多媒体数据失败: {str(e)}")
            # 如果获取多媒体数据失败，使用默认值
            pass
        
        return card_data


# 创建全局策略实例
match_card_strategy = MatchCardStrategy()