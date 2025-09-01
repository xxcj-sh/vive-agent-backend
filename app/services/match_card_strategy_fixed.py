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
            return self._create_sample_housing_cards_for_seeker(page, page_size)
        elif user_role == "provider":
            # 房东看到的是租客的需求信息
            return self._create_sample_tenant_cards_for_provider(page, page_size)
        else:
            # 默认返回房源卡片
            return self._create_sample_housing_cards_for_seeker(page, page_size)
    
    def _get_dating_cards(
        self, 
        user_role: str, 
        page: int, 
        page_size: int, 
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取交友匹配卡片"""
        
        # 交友场景：显示其他用户的个人信息
        return self._create_sample_dating_cards(page, page_size)
    
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
            return self._create_sample_activity_cards_for_seeker(page, page_size)
        elif user_role == "provider":
            # 组织者看到的是参与者的信息
            return self._create_sample_participant_cards_for_organizer(page, page_size)
        else:
            # 默认返回活动卡片
            return self._create_sample_activity_cards_for_seeker(page, page_size)
    
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


# 创建全局策略实例
match_card_strategy = MatchCardStrategy()