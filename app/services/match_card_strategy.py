"""
匹配卡片策略服务
负责控制返回匹配卡片的策略和逻辑
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import random
import time
from app.services.data_adapter import data_service
from app.services.mock_data_backup import mock_data_service


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
        
        # 获取基础房源数据
        base_result = data_service.get_cards("housing", user_role, page, page_size)
        
        if not base_result or not base_result.get("list"):
            # 如果没有数据，创建一些示例房源卡片
            return self._create_sample_housing_cards(page, page_size)
        
        # 应用房源匹配策略
        cards = base_result["list"]
        
        # 基于用户偏好过滤和排序
        if current_user:
            cards = self._apply_housing_preferences(cards, current_user)
        
        # 基于位置距离排序
        cards = self._sort_by_location(cards, current_user)
        
        # 添加推荐理由
        cards = self._add_recommendation_reasons(cards, "housing")
        
        return {
            "total": len(cards),
            "list": cards[0:page_size],  # 重新分页
            "page": page,
            "pageSize": page_size,
            "strategy": "housing_optimized"
        }
    
    def _get_dating_cards(
        self, 
        user_role: str, 
        page: int, 
        page_size: int, 
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取交友匹配卡片"""
        
        base_result = data_service.get_cards("dating", user_role, page, page_size)
        
        if not base_result or not base_result.get("list"):
            return self._create_sample_dating_cards(page, page_size)
        
        cards = base_result["list"]
        
        # 应用交友匹配策略
        if current_user:
            cards = self._apply_dating_compatibility(cards, current_user)
        
        cards = self._add_recommendation_reasons(cards, "dating")
        
        return {
            "total": len(cards),
            "list": cards[0:page_size],
            "page": page,
            "pageSize": page_size,
            "strategy": "dating_compatibility"
        }
    
    def _get_activity_cards(
        self, 
        user_role: str, 
        page: int, 
        page_size: int, 
        current_user: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取活动匹配卡片"""
        
        base_result = data_service.get_cards("activity", user_role, page, page_size)
        
        if not base_result or not base_result.get("list"):
            return self._create_sample_activity_cards(page, page_size)
        
        cards = base_result["list"]
        
        # 应用活动匹配策略
        if current_user:
            cards = self._apply_activity_interests(cards, current_user)
        
        cards = self._add_recommendation_reasons(cards, "activity")
        
        return {
            "total": len(cards),
            "list": cards[0:page_size],
            "page": page,
            "pageSize": page_size,
            "strategy": "activity_interests"
        }
    
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
    
    def _apply_housing_preferences(self, cards: List[Dict], current_user: Dict) -> List[Dict]:
        """应用房源偏好过滤"""
        if not current_user or not cards:
            return cards
        
        # 示例：基于预算、位置偏好等过滤
        user_preferences = current_user.get("preferences", {})
        budget_range = user_preferences.get("budgetRange")
        preferred_areas = user_preferences.get("preferredAreas", [])
        
        filtered_cards = []
        for card in cards:
            house_info = card.get("houseInfo", {})
            
            # 预算过滤
            if budget_range:
                rent = house_info.get("rent", 0)
                if budget_range[0] <= rent <= budget_range[1]:
                    filtered_cards.append(card)
            else:
                filtered_cards.append(card)
        
        return filtered_cards
    
    def _apply_dating_compatibility(self, cards: List[Dict], current_user: Dict) -> List[Dict]:
        """应用交友兼容性算法"""
        if not current_user or not cards:
            return cards
        
        user_interests = set(current_user.get("interests", []))
        user_age = current_user.get("age", 25)
        
        # 计算兼容性分数并排序
        scored_cards = []
        for card in cards:
            card_interests = set(card.get("interests", []))
            card_age = card.get("age", 25)
            
            # 兴趣匹配度
            interest_score = len(user_interests & card_interests) / max(len(user_interests | card_interests), 1)
            
            # 年龄匹配度
            age_diff = abs(user_age - card_age)
            age_score = max(0, 1 - age_diff / 10)
            
            # 综合分数
            total_score = interest_score * 0.6 + age_score * 0.4
            
            scored_cards.append((total_score, card))
        
        # 按分数排序
        scored_cards.sort(key=lambda x: x[0], reverse=True)
        return [card for score, card in scored_cards]
    
    def _apply_activity_interests(self, cards: List[Dict], current_user: Dict) -> List[Dict]:
        """应用活动兴趣匹配"""
        if not current_user or not cards:
            return cards
        
        user_interests = set(current_user.get("interests", []))
        
        # 按兴趣匹配度排序
        scored_cards = []
        for card in cards:
            activity_tags = set(card.get("tags", []))
            activity_category = card.get("category", "")
            
            # 计算匹配度
            tag_score = len(user_interests & activity_tags) / max(len(activity_tags), 1)
            category_score = 1 if activity_category in user_interests else 0
            
            total_score = tag_score * 0.7 + category_score * 0.3
            scored_cards.append((total_score, card))
        
        scored_cards.sort(key=lambda x: x[0], reverse=True)
        return [card for score, card in scored_cards]
    
    def _sort_by_location(self, cards: List[Dict], current_user: Optional[Dict]) -> List[Dict]:
        """基于位置距离排序"""
        if not current_user or not cards:
            return cards
        
        user_location = current_user.get("location", [])
        if not user_location:
            return cards
        
        # 简化的位置匹配逻辑
        def location_priority(card):
            card_location = card.get("location", [])
            if not card_location:
                return 999
            
            # 同城市优先级最高
            if len(user_location) >= 1 and len(card_location) >= 1:
                if user_location[0] == card_location[0]:
                    return 1
            
            return 2
        
        return sorted(cards, key=location_priority)
    
    def _add_recommendation_reasons(self, cards: List[Dict], match_type: str) -> List[Dict]:
        """为卡片添加推荐理由"""
        reasons_pool = {
            "housing": [
                "位置便利，交通方便",
                "价格合理，性价比高",
                "房源条件优质",
                "周边配套完善",
                "符合您的预算范围"
            ],
            "dating": [
                "兴趣爱好相似",
                "年龄匹配度高",
                "生活方式相近",
                "价值观相符",
                "地理位置接近"
            ],
            "activity": [
                "符合您的兴趣偏好",
                "时间安排合适",
                "活动类型匹配",
                "地点便利",
                "参与人群相似"
            ]
        }
        
        reasons = reasons_pool.get(match_type, ["推荐给您"])
        
        for card in cards:
            if "recommendReason" not in card:
                card["recommendReason"] = random.choice(reasons)
        
        return cards
    
    def _create_sample_housing_cards(self, page: int, page_size: int) -> Dict[str, Any]:
        """创建示例房源卡片"""
        sample_cards = []
        
        for i in range(page_size):
            card_id = f"housing_sample_{(page-1)*page_size + i + 1}"
            card = {
                "id": card_id,
                "matchType": "housing",
                "userRole": "provider",
                "title": f"精装两居室 - 样例房源 {i+1}",
                "houseInfo": {
                    "rent": random.randint(3000, 8000),
                    "area": random.randint(60, 120),
                    "rooms": f"{random.randint(1,3)}室{random.randint(1,2)}厅",
                    "floor": f"{random.randint(1,20)}/{random.randint(20,30)}层",
                    "direction": random.choice(["南北通透", "朝南", "朝北", "东西向"]),
                    "decoration": random.choice(["精装修", "简装修", "毛坯"]),
                    "facilities": ["空调", "洗衣机", "冰箱", "热水器"],
                    "images": [
                        f"https://picsum.photos/400/300?random={card_id}_1",
                        f"https://picsum.photos/400/300?random={card_id}_2"
                    ],
                    "videoUrl": "https://cdn.pixabay.com/video/2024/02/03/199109-909564730_tiny.mp4"
                },
                "location": ["北京市", "朝阳区", f"示例小区{i+1}"],
                "contactInfo": {
                    "name": f"房东{i+1}",
                    "phone": f"138****{1000+i:04d}"
                },
                "publishTime": int(time.time()) - random.randint(0, 86400*7),
                "recommendReason": "位置便利，交通方便"
            }
            sample_cards.append(card)
        
        return {
            "total": 50,  # 假设总共有50条数据
            "list": sample_cards,
            "page": page,
            "pageSize": page_size,
            "strategy": "sample_housing"
        }
    
    def _create_sample_dating_cards(self, page: int, page_size: int) -> Dict[str, Any]:
        """创建示例交友卡片"""
        sample_cards = []
        
        names = ["小明", "小红", "小李", "小王", "小张", "小陈", "小刘", "小黄"]
        occupations = ["软件工程师", "设计师", "教师", "医生", "律师", "销售", "产品经理", "运营"]
        interests = ["旅行", "摄影", "音乐", "电影", "运动", "读书", "美食", "游戏"]
        
        for i in range(page_size):
            card_id = f"dating_sample_{(page-1)*page_size + i + 1}"
            card = {
                "id": card_id,
                "matchType": "dating",
                "userRole": "user",
                "nickName": random.choice(names),
                "age": random.randint(22, 35),
                "gender": random.randint(1, 2),
                "occupation": random.choice(occupations),
                "location": ["上海市", "徐汇区"],
                "bio": f"热爱生活，喜欢{random.choice(interests)}",
                "interests": random.sample(interests, 3),
                "avatarUrl": f"https://picsum.photos/200/200?random=avatar_{card_id}",
                "images": [
                    f"https://picsum.photos/300/400?random={card_id}_1",
                    f"https://picsum.photos/300/400?random={card_id}_2"
                ],
                "education": random.choice(["本科", "硕士", "博士"]),
                "height": random.randint(160, 185),
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
    
    def _create_sample_activity_cards(self, page: int, page_size: int) -> Dict[str, Any]:
        """创建示例活动卡片"""
        sample_cards = []
        
        activities = ["户外徒步", "摄影聚会", "读书分享", "美食探店", "运动健身", "音乐会", "展览参观", "技术交流"]
        locations = ["朝阳公园", "奥林匹克公园", "颐和园", "故宫", "798艺术区", "三里屯", "王府井", "西单"]
        
        for i in range(page_size):
            card_id = f"activity_sample_{(page-1)*page_size + i + 1}"
            activity_name = random.choice(activities)
            card = {
                "id": card_id,
                "matchType": "activity",
                "userRole": "organizer",
                "title": f"{activity_name} - 周末聚会",
                "description": f"欢迎参加{activity_name}活动，一起度过愉快的周末时光",
                "category": activity_name.split()[0] if " " in activity_name else activity_name,
                "tags": [activity_name, "周末", "聚会"],
                "location": ["北京市", "朝阳区", random.choice(locations)],
                "time": {
                    "startTime": int(time.time()) + random.randint(86400, 86400*7),
                    "duration": random.randint(2, 6)
                },
                "participants": {
                    "current": random.randint(5, 15),
                    "max": random.randint(20, 50)
                },
                "fee": random.choice([0, 50, 100, 200]),
                "organizer": {
                    "name": f"活动组织者{i+1}",
                    "avatar": f"https://picsum.photos/100/100?random=org_{card_id}"
                },
                "images": [f"https://picsum.photos/400/300?random={card_id}"],
                "recommendReason": "符合您的兴趣偏好"
            }
            sample_cards.append(card)
        
        return {
            "total": 80,
            "list": sample_cards,
            "page": page,
            "pageSize": page_size,
            "strategy": "sample_activity"
        }


# 创建全局策略实例
match_card_strategy = MatchCardStrategy()m.photos/400/300?random={card_id}"],
                "recommendReason": "符合您的兴趣偏好"
            }
            sample_cards.append(card)
        
        return {
            "total": 80,
            "list": sample_cards,
            "page": page,
            "pageSize": page_size,
            "strategy": "sample_activity"
        }


# 创建全局策略实例
match_card_strategy = MatchCardStrategy()            "strategy": "sample_activity"
        }


# 创建全局策略实例
match_card_strategy = MatchCardStrategy()