"""
匹配卡片策略服务
负责控制返回匹配卡片的策略和逻辑
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import random
import time

from app.services.data_adapter import data_service
from app.services.media_service import media_service
from app.models.user import User
from app.models.user_profile_db import UserProfile
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
            # 根据匹配类型选择不同的策略
            if match_type == "housing":
                return self._get_housing_cards(user_role, page, page_size, current_user)
            elif match_type == "dating":
                return self._get_dating_cards(user_role, page, page_size, current_user)
            elif match_type == "activity":
                return self._get_activity_cards(user_role, page, page_size, current_user)
            else:
                # 默认策略
                return self._get_default_cards(match_type, user_role, page, page_size, current_user)
                
        except Exception as e:
            print(f"匹配卡片策略执行失败: {str(e)}")
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
            landlords_query = db.query(User).join(UserProfile).filter(
                UserProfile.role_type.like('%provider%'),
                UserProfile.scene_type == 'housing'
            )
            
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
            print(f"数据库查询失败，使用样本数据: {str(e)}")
            # 降级到样本数据
            return self._create_sample_housing_cards_for_seeker(page, page_size)
    
    def _get_tenant_cards_for_provider(self, page: int, page_size: int, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从数据库获取房东视角的租客卡片（显示租客的需求信息）"""
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 查询租客用户（寻找房源的用户）
            tenants_query = db.query(User).join(UserProfile).filter(
                UserProfile.role_type.like('%seeker%'),
                UserProfile.scene_type == 'housing'
            )
            
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
            print(f"数据库查询失败，使用样本数据: {str(e)}")
            # 降级到样本数据
            return self._create_sample_tenant_cards_for_provider(page, page_size)
    
    def _create_sample_housing_cards_for_seeker(self, page: int, page_size: int) -> Dict[str, Any]:
        """创建租客视角的房源卡片（显示房东的房源信息）"""
        sample_cards = []
        
        for i in range(page_size):
            card_id = f"housing_sample_{(page-1)*page_size + i + 1}"
            
            # 生成多媒体数据
            media_data = self._generate_sample_media_data(card_id, "housing")
            
            # 租客视角：显示房东的房源信息
            card = {
                "id": card_id,
                "matchType": "housing",
                "userRole": "seeker",  # 当前用户是租客
                # 房源基本信息（前端Card组件需要的字段）
                "houseImage": media_data["house_images"][0] if media_data["house_images"] else "",
                "houseInfo": {
                    "price": random.randint(3000, 8000),
                    "area": random.randint(60, 120),
                    "orientation": random.choice(["南北通透", "朝南", "朝北", "东西向"]),
                    "hasElevator": random.choice([True, False]),
                    "location": f"朝阳区",
                    "community": f"示例小区{i+1}",
                    # 房源多媒体数据
                    "images": media_data["house_images"],
                    "videoUrl": media_data["house_video_url"]
                },
                # 房东信息
                "landlordInfo": {
                    "avatar": media_data["avatar_url"],
                    "name": f"房东{i+1}",
                    "age": random.randint(25, 45)
                },
                # 详情页面需要的额外信息
                "area": random.randint(60, 120),
                "orientation": random.choice(["南北通透", "朝南", "朝北", "东西向"]),
                "floor": f"{random.randint(1,20)}/{random.randint(20,30)}层",
                "hasElevator": random.choice([True, False]),
                "decoration": random.choice(["精装修", "简装修", "毛坯"]),
                "price": random.randint(3000, 8000),
                "deposit": f"{random.randint(1,3)}押{random.randint(1,3)}付",
                "community": f"示例小区{i+1}",
                "location": f"朝阳区示例小区{i+1}",
                # 兼容字段
                "title": f"精装{random.choice(['一', '二', '三'])}居室 - 样例房源 {i+1}",
                "publishTime": int(time.time()) - random.randint(0, 86400*7),
                "recommendReason": "位置便利，交通方便"
            }
            sample_cards.append(card)
        
        return {
            "total": 50,  # 假设总共有50条数据
            "list": sample_cards,
            "page": page,
            "pageSize": page_size,
            "strategy": "housing_seeker_view"
        }
    
    def _create_sample_tenant_cards_for_provider(self, page: int, page_size: int) -> Dict[str, Any]:
        """创建房东视角的租客卡片（显示租客的需求信息）"""
        sample_cards = []
        
        occupations = ["软件工程师", "设计师", "教师", "医生", "律师", "销售", "产品经理", "运营"]
        interests = ["旅行", "摄影", "音乐", "电影", "运动", "读书", "美食", "游戏"]
        
        for i in range(page_size):
            card_id = f"tenant_sample_{(page-1)*page_size + i + 1}"
            
            # 生成多媒体数据
            media_data = self._generate_sample_media_data(card_id, "dating")
            
            # 房东视角：显示租客的个人信息和租房需求
            card = {
                "id": card_id,
                "matchType": "housing",
                "userRole": "provider",  # 当前用户是房东
                # 租客基本信息
                "name": f"租客{i+1}",
                "age": random.randint(22, 35),
                "occupation": random.choice(occupations),
                "avatar": media_data["avatar_url"],
                "videoUrl": media_data["video_url"],
                "images": media_data["images"],
                # 租房需求信息
                "tenantInfo": {
                    "budget": random.randint(3000, 8000),
                    "leaseDuration": random.choice(["半年", "一年", "两年", "长期"]),
                    "moveInDate": "随时",
                    "priceRange": f"{random.randint(3000, 5000)}-{random.randint(5000, 8000)}元",
                    "leaseTerm": random.choice(["半年", "一年", "两年"])
                },
                # 详情页面信息
                "location": ["北京市", "朝阳区"],
                "bio": f"工作稳定，爱好{random.choice(interests)}，寻找合适的住所",
                "interests": random.sample(interests, 3),
                "priceRange": f"{random.randint(3000, 5000)}-{random.randint(5000, 8000)}元",
                "leaseTerm": random.choice(["半年", "一年", "两年"]),
                "moveInDate": "随时入住",
                "recommendReason": "工作稳定，信誉良好"
            }
            sample_cards.append(card)
        
        return {
            "total": 30,  # 假设总共有30个租客
            "list": sample_cards,
            "page": page,
            "pageSize": page_size,
            "strategy": "housing_provider_view"
        }
    
    def _get_dating_cards_from_db(self, page: int, page_size: int, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从数据库获取交友匹配卡片"""
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 查询交友用户，排除当前用户
            current_user_id = current_user.get('id') if current_user else None
            
            dating_users_query = db.query(User).join(UserProfile).filter(
                UserProfile.scene_type == 'dating'
            )
            
            if current_user_id:
                dating_users_query = dating_users_query.filter(User.id != current_user_id)
            
            # 分页查询
            offset = (page - 1) * page_size
            dating_users = dating_users_query.offset(offset).limit(page_size).all()
            total_count = dating_users_query.count()
            
            # 转换为卡片数据
            cards = []
            for user in dating_users:
                card_data = self._convert_user_to_dating_card(user)
                # 添加多媒体数据
                card_data = self._enrich_card_with_media(card_data, str(user.id))
                cards.append(card_data)
            
            return {
                "total": total_count,
                "list": cards,
                "page": page,
                "pageSize": page_size,
                "strategy": "dating_db"
            }
            
        except Exception as e:
            print(f"数据库查询失败，使用样本数据: {str(e)}")
            # 降级到样本数据
            return self._create_sample_dating_cards(page, page_size)
    
    def _get_activity_cards_for_seeker(self, page: int, page_size: int, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从数据库获取参与者视角的活动卡片"""
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 查询活动组织者
            organizers_query = db.query(User).join(UserProfile).filter(
                UserProfile.role_type.like('%provider%'),
                UserProfile.scene_type == 'activity'
            )
            
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
            print(f"数据库查询失败，使用样本数据: {str(e)}")
            # 降级到样本数据
            return self._create_sample_activity_cards_for_seeker(page, page_size)
    
    def _get_participant_cards_for_organizer(self, page: int, page_size: int, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从数据库获取组织者视角的参与者卡片"""
        try:
            # 获取数据库会话
            db = next(get_db())
            
            # 查询活动参与者
            participants_query = db.query(User).join(UserProfile).filter(
                UserProfile.role_type.like('%seeker%'),
                UserProfile.scene_type == 'activity'
            )
            
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
            print(f"数据库查询失败，使用样本数据: {str(e)}")
            # 降级到样本数据
            return self._create_sample_participant_cards_for_organizer(page, page_size)
    
    def _create_sample_dating_cards(self, page: int, page_size: int) -> Dict[str, Any]:
        """创建示例交友卡片，包含多媒体数据支持"""
        sample_cards = []
        
        names = ["小明", "小红", "小李", "小王", "小张", "小陈", "小刘", "小黄"]
        occupations = ["软件工程师", "设计师", "教师", "医生", "律师", "销售", "产品经理", "运营"]
        interests = ["旅行", "摄影", "音乐", "电影", "运动", "读书", "美食", "游戏"]
        
        for i in range(page_size):
            card_id = f"dating_sample_{(page-1)*page_size + i + 1}"
            
            # 生成多媒体数据
            media_data = self._generate_sample_media_data(card_id, "dating")
            
            card = {
                "id": card_id,
                "matchType": "dating",
                "userRole": "user",
                "name": random.choice(names),
                "nickName": random.choice(names),
                "age": random.randint(22, 35),
                "gender": random.randint(1, 2),
                "occupation": random.choice(occupations),
                "location": ["上海市", "徐汇区"],
                "bio": f"热爱生活，喜欢{random.choice(interests)}",
                "interests": random.sample(interests, 3),
                "hobbies": random.sample(interests, 3),
                # 多媒体数据
                "avatar": media_data["avatar_url"],
                "avatarUrl": media_data["avatar_url"],
                "videoUrl": media_data["video_url"],
                "images": media_data["images"],
                # 交友特定信息
                "education": random.choice(["本科", "硕士", "博士"]),
                "height": random.randint(160, 185),
                "income": random.choice(["5-10万", "10-20万", "20-30万", "30万以上"]),
                "lookingFor": "寻找志同道合的朋友，一起分享生活的美好",
                "recommendReason": "兴趣爱好相似"
            }
            sample_cards.append(card)
        
        return {
            "total": 100,
            "list": sample_cards,
            "page": page,
            "pageSize": page_size,
            "strategy": "sample_dating"
        }
    
    def _create_sample_activity_cards_for_seeker(self, page: int, page_size: int) -> Dict[str, Any]:
        """创建参与者视角的活动卡片（显示组织者的活动信息）"""
        sample_cards = []
        
        activities = ["户外徒步", "摄影聚会", "读书分享", "美食探店", "运动健身", "音乐会", "展览参观", "技术交流"]
        locations = ["朝阳公园", "奥林匹克公园", "颐和园", "故宫", "798艺术区", "三里屯", "王府井", "西单"]
        
        for i in range(page_size):
            card_id = f"activity_sample_{(page-1)*page_size + i + 1}"
            activity_name = random.choice(activities)
            
            # 生成多媒体数据
            media_data = self._generate_sample_media_data(card_id, "activity")
            
            card = {
                "id": card_id,
                "matchType": "activity",
                "userRole": "seeker",  # 当前用户是参与者
                "name": f"活动组织者{i+1}",
                "age": random.randint(25, 40),
                "occupation": random.choice(["活动策划师", "健身教练", "摄影师", "导游", "老师"]),
                # 多媒体数据
                "avatar": media_data["avatar_url"],
                "videoUrl": media_data["video_url"],
                "images": media_data["images"],
                # 活动信息
                "activityName": f"{activity_name} - 周末聚会",
                "activityType": activity_name.split()[0] if " " in activity_name else activity_name,
                "activityTime": "周末上午 9:00-12:00",
                "activityLocation": random.choice(locations),
                "activityPrice": random.choice([0, 50, 100, 200]),
                "activityDuration": f"{random.randint(2, 6)}小时",
                "activityMaxParticipants": random.randint(20, 50),
                "activityDifficulty": random.choice(["初级", "中级", "高级"]),
                "activityIncludes": ["专业指导", "活动用品", "纪念品"],
                "activityDescription": f"欢迎参加{activity_name}活动，一起度过愉快的周末时光。我们将提供专业的指导和完善的服务，让每位参与者都能收获满满。",
                "recommendReason": "符合您的兴趣偏好"
            }
            sample_cards.append(card)
        
        return {
            "total": 80,
            "list": sample_cards,
            "page": page,
            "pageSize": page_size,
            "strategy": "activity_seeker_view"
        }
    
    def _create_sample_participant_cards_for_organizer(self, page: int, page_size: int) -> Dict[str, Any]:
        """创建组织者视角的参与者卡片（显示参与者的信息）"""
        sample_cards = []
        
        names = ["小明", "小红", "小李", "小王", "小张", "小陈", "小刘", "小黄"]
        occupations = ["软件工程师", "设计师", "教师", "医生", "律师", "销售", "产品经理", "运营"]
        interests = ["旅行", "摄影", "音乐", "电影", "运动", "读书", "美食", "游戏"]
        
        for i in range(page_size):
            card_id = f"participant_sample_{(page-1)*page_size + i + 1}"
            
            # 生成多媒体数据
            media_data = self._generate_sample_media_data(card_id, "dating")
            
            # 组织者视角：显示参与者的个人信息和活动偏好
            card = {
                "id": card_id,
                "matchType": "activity",
                "userRole": "provider",  # 当前用户是组织者
                # 参与者基本信息
                "name": random.choice(names),
                "age": random.randint(22, 35),
                "occupation": random.choice(occupations),
                "avatar": media_data["avatar_url"],
                "videoUrl": media_data["video_url"],
                "images": media_data["images"],
                # 活动偏好信息
                "preferredActivity": random.choice(["户外运动", "文化艺术", "美食探索", "学习交流"]),
                "budgetRange": f"{random.randint(50, 200)}-{random.randint(200, 500)}元",
                "preferredTime": random.choice(["周末上午", "周末下午", "工作日晚上"]),
                "preferredLocation": random.choice(["朝阳区", "海淀区", "西城区", "东城区"]),
                # 详情页面信息
                "location": ["北京市", random.choice(["朝阳区", "海淀区", "西城区"])],
                "bio": f"热爱{random.choice(interests)}，希望通过活动结识志同道合的朋友",
                "interests": random.sample(interests, 3),
                "recommendReason": "活动参与积极，兴趣匹配"
            }
            sample_cards.append(card)
        
        return {
            "total": 60,
            "list": sample_cards,
            "page": page,
            "pageSize": page_size,
            "strategy": "activity_organizer_view"
        }
    
    def _generate_sample_media_data(self, card_id: str, match_type: str) -> Dict[str, Any]:
        """生成示例多媒体数据"""
        base_media = {
            "avatar_url": f"https://images.unsplash.com/photo-{random.randint(1500000000, 1700000000)}-{random.randint(100000000, 999999999)}?w=400&h=400&fit=crop&crop=face",
            "video_url": "",
            "images": []
        }
        
        if match_type == "housing":
            # 房源相关多媒体
            base_media.update({
                "house_images": [
                    f"https://images.unsplash.com/photo-1522708323590-d2db1a6ee4ea?w=800&h=600&fit=crop&random={card_id}_house_1",
                    f"https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800&h=600&fit=crop&random={card_id}_house_2",
                    f"https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800&h=600&fit=crop&random={card_id}_house_3"
                ],
                "house_video_url": "https://cdn.pixabay.com/video/2024/02/03/199109-909564730_tiny.mp4" if random.choice([True, False]) else "",
                "images": [
                    f"https://images.unsplash.com/photo-{random.randint(1500000000, 1700000000)}-{random.randint(100000000, 999999999)}?w=400&h=600&fit=crop&random={card_id}_profile_1",
                    f"https://images.unsplash.com/photo-{random.randint(1500000000, 1700000000)}-{random.randint(100000000, 999999999)}?w=400&h=600&fit=crop&random={card_id}_profile_2"
                ]
            })
        elif match_type == "dating":
            # 交友相关多媒体
            base_media.update({
                "images": [
                    f"https://images.unsplash.com/photo-{random.randint(1500000000, 1700000000)}-{random.randint(100000000, 999999999)}?w=400&h=600&fit=crop&crop=face&random={card_id}_dating_1",
                    f"https://images.unsplash.com/photo-{random.randint(1500000000, 1700000000)}-{random.randint(100000000, 999999999)}?w=400&h=600&fit=crop&crop=face&random={card_id}_dating_2",
                    f"https://images.unsplash.com/photo-{random.randint(1500000000, 1700000000)}-{random.randint(100000000, 999999999)}?w=400&h=600&fit=crop&crop=face&random={card_id}_dating_3"
                ],
                "video_url": "https://cdn.pixabay.com/video/2024/01/15/196708-906264126_tiny.mp4" if random.choice([True, False]) else ""
            })
        elif match_type == "activity":
            # 活动相关多媒体
            base_media.update({
                "images": [
                    f"https://images.unsplash.com/photo-{random.randint(1500000000, 1700000000)}-{random.randint(100000000, 999999999)}?w=400&h=600&fit=crop&random={card_id}_activity_1",
                    f"https://images.unsplash.com/photo-{random.randint(1500000000, 1700000000)}-{random.randint(100000000, 999999999)}?w=400&h=600&fit=crop&random={card_id}_activity_2"
                ],
                "video_url": "https://cdn.pixabay.com/video/2024/03/10/203847-920123456_tiny.mp4" if random.choice([True, False]) else ""
            })
        
        return base_media
    
    def _convert_user_to_housing_card_for_seeker(self, landlord: User) -> Dict[str, Any]:
        """将房东用户数据转换为租客视角的房源卡片"""
        # 获取第一个资料，如果有多个的话
        profile = landlord.profiles[0] if landlord.profiles else None
        profile_data = profile.profile_data if profile and profile.profile_data else {}
        print("landlord.id:", landlord.id)
        return {
            "id": f"housing_db_{landlord.id}",
            "matchType": "housing",
            "userRole": "seeker",
            # 房源基本信息
            "houseImage": "",  # 将通过多媒体服务填充
            "houseInfo": {
                "price": profile_data.get('housing_price', 5000),
                "area": profile_data.get('housing_area', 80),
                "orientation": profile_data.get('housing_orientation', '南北通透'),
                "hasElevator": profile_data.get('housing_has_elevator', True),
                "location": profile_data.get('location', '朝阳区'),
                "community": profile_data.get('housing_community', '未知小区'),
                "images": [],  # 将通过多媒体服务填充
                "videoUrl": ""  # 将通过多媒体服务填充
            },
            # 房东信息
            "landlordInfo": {
                "avatar": "",  # 将通过多媒体服务填充
                "name": landlord.nick_name or landlord.username or f"用户{landlord.id}",
                "age": profile_data.get('age', 30),
                "user_id": landlord.id
            },
            # 详情页面需要的额外信息
            "area": profile_data.get('housing_area', 80),
            "orientation": profile_data.get('housing_orientation', '南北通透'),
            "floor": profile_data.get('housing_floor', '10/20层'),
            "hasElevator": profile_data.get('housing_has_elevator', True),
            "decoration": profile_data.get('housing_decoration', '精装修'),
            "price": profile_data.get('housing_price', 5000),
            "deposit": profile_data.get('housing_deposit', '1押1付'),
            "community": profile_data.get('housing_community', '未知小区'),
            "location": profile_data.get('location', '朝阳区'),
            "title": f"{profile_data.get('housing_type', '两')}居室 - {profile_data.get('housing_community', '未知小区')}",
            "publishTime": int(landlord.created_at.timestamp()) if landlord.created_at else 0,
            "recommendReason": "位置便利，交通方便"
        }
    
    def _convert_user_to_tenant_card_for_provider(self, tenant: User) -> Dict[str, Any]:
        """将租客用户数据转换为房东视角的租客卡片"""
        # 获取第一个资料，如果有多个的话
        profile = tenant.profiles[0] if tenant.profiles else None
        profile_data = profile.profile_data if profile and profile.profile_data else {}
        
        return {
            "id": f"tenant_db_{tenant.id}",
            "matchType": "housing",
            "userRole": "provider",
            # 租客基本信息
            "name": tenant.nick_name or tenant.username or f"用户{tenant.id}",
            "age": profile_data.get('age', 25),
            "occupation": profile_data.get('occupation', '未知职业'),
            "avatar": "",  # 将通过多媒体服务填充
            "videoUrl": "",  # 将通过多媒体服务填充
            "images": [],  # 将通过多媒体服务填充
            # 租房需求信息
            "tenantInfo": {
                "budget": getattr(profile, 'housing_budget', 5000),
                "leaseDuration": getattr(profile, 'housing_lease_duration', '一年'),
                "moveInDate": getattr(profile, 'housing_move_in_date', '随时'),
                "priceRange": f"{getattr(profile, 'housing_budget_min', 3000)}-{getattr(profile, 'housing_budget_max', 8000)}元",
                "leaseTerm": getattr(profile, 'housing_lease_duration', '一年')
            },
            # 详情页面信息
            "location": [getattr(profile, 'city', '北京市'), getattr(profile, 'district', '朝阳区')],
            "bio": getattr(profile, 'bio', '工作稳定，寻找合适的住所'),
            "interests": getattr(profile, 'interests', '').split(',') if getattr(profile, 'interests', '') else [],
            "priceRange": f"{getattr(profile, 'housing_budget_min', 3000)}-{getattr(profile, 'housing_budget_max', 8000)}元",
            "leaseTerm": getattr(profile, 'housing_lease_duration', '一年'),
            "moveInDate": getattr(profile, 'housing_move_in_date', '随时入住'),
            "recommendReason": "工作稳定，信誉良好"
        }
    
    def _convert_user_to_dating_card(self, user: User) -> Dict[str, Any]:
        """将用户数据转换为交友卡片"""
        # 获取第一个资料，如果有多个的话
        profile = user.profiles[0] if user.profiles else None
        profile_data = profile.profile_data if profile and profile.profile_data else {}
        
        return {
            "id": f"dating_db_{user.id}",
            "matchType": "dating",
            "userRole": "user",
            "name": user.nickname or user.username or f"用户{user.id}",
            "nickName": user.nickname or user.username,
            "age": getattr(profile, 'age', 25),
            "gender": getattr(profile, 'gender', Gender.MALE).value if hasattr(profile, 'gender') else 1,
            "occupation": getattr(profile, 'occupation', '未知职业'),
            "location": [getattr(profile, 'city', '北京市'), getattr(profile, 'district', '朝阳区')],
            "bio": getattr(profile, 'bio', '热爱生活，寻找志同道合的朋友'),
            "interests": getattr(profile, 'interests', '').split(',') if getattr(profile, 'interests', '') else [],
            "hobbies": getattr(profile, 'hobbies', '').split(',') if getattr(profile, 'hobbies', '') else [],
            # 多媒体数据（将通过多媒体服务填充）
            "avatar": "",
            "avatarUrl": "",
            "videoUrl": "",
            "images": [],
            # 交友特定信息
            "education": getattr(profile, 'education', '本科'),
            "height": getattr(profile, 'height', 170),
            "income": getattr(profile, 'income_range', '10-20万'),
            "lookingFor": getattr(profile, 'looking_for', '寻找志同道合的朋友'),
            "recommendReason": "兴趣爱好相似"
        }
    
    def _convert_user_to_activity_card_for_seeker(self, organizer: User) -> Dict[str, Any]:
        """将组织者用户数据转换为参与者视角的活动卡片"""
        # 获取第一个资料，如果有多个的话
        profile = organizer.profiles[0] if organizer.profiles else None
        profile_data = profile.profile_data if profile and profile.profile_data else {}
        
        return {
            "id": f"activity_db_{organizer.id}",
            "matchType": "activity",
            "userRole": "seeker",
            "name": organizer.nickname or organizer.username or f"组织者{organizer.id}",
            "age": getattr(profile, 'age', 30),
            "occupation": getattr(profile, 'occupation', '活动策划师'),
            # 多媒体数据（将通过多媒体服务填充）
            "avatar": "",
            "videoUrl": "",
            "images": [],
            # 活动信息
            "activityName": getattr(profile, 'activity_name', '周末户外活动'),
            "activityType": getattr(profile, 'activity_type', '户外运动'),
            "activityTime": getattr(profile, 'activity_time', '周末上午 9:00-12:00'),
            "activityLocation": getattr(profile, 'activity_location', '朝阳公园'),
            "activityPrice": getattr(profile, 'activity_price', 100),
            "activityDuration": getattr(profile, 'activity_duration', '3小时'),
            "activityMaxParticipants": getattr(profile, 'activity_max_participants', 20),
            "activityDifficulty": getattr(profile, 'activity_difficulty', '初级'),
            "activityIncludes": getattr(profile, 'activity_includes', '专业指导,活动用品').split(','),
            "activityDescription": getattr(profile, 'activity_description', '欢迎参加我们的活动，一起度过愉快的时光'),
            "recommendReason": "符合您的兴趣偏好"
        }
    
    def _convert_user_to_participant_card_for_organizer(self, participant: User) -> Dict[str, Any]:
        """将参与者用户数据转换为组织者视角的参与者卡片"""
        # 获取第一个资料，如果有多个的话
        profile = participant.profiles[0] if participant.profiles else None
        profile_data = profile.profile_data if profile and profile.profile_data else {}
        
        return {
            "id": f"participant_db_{participant.id}",
            "matchType": "activity",
            "userRole": "provider",
            # 参与者基本信息
            "name": participant.nickname or participant.username or f"用户{participant.id}",
            "age": getattr(profile, 'age', 25),
            "occupation": getattr(profile, 'occupation', '未知职业'),
            "avatar": "",  # 将通过多媒体服务填充
            "videoUrl": "",  # 将通过多媒体服务填充
            "images": [],  # 将通过多媒体服务填充
            # 活动偏好信息
            "preferredActivity": getattr(profile, 'preferred_activity_type', '户外运动'),
            "budgetRange": f"{getattr(profile, 'activity_budget_min', 50)}-{getattr(profile, 'activity_budget_max', 200)}元",
            "preferredTime": getattr(profile, 'preferred_activity_time', '周末上午'),
            "preferredLocation": getattr(profile, 'preferred_activity_location', '朝阳区'),
            # 详情页面信息
            "location": [getattr(profile, 'city', '北京市'), getattr(profile, 'district', '朝阳区')],
            "bio": getattr(profile, 'bio', '热爱运动，希望通过活动结识朋友'),
            "interests": getattr(profile, 'interests', '').split(',') if getattr(profile, 'interests', '') else [],
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