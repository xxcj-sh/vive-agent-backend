"""
咖啡店推荐服务
基于用户画像、地理位置、时间偏好等数据，智能推荐咖啡店
"""

import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.ai_skill import (
    CoffeeShopRecommendation, 
    CoffeeShopRecommendationRequest, 
    CoffeeShopRecommendationResponse
)
from app.models.user_profile import UserProfile
from app.services.user_card_service import UserCardService
from app.database import get_db


class CoffeeRecommendationService:
    """咖啡店推荐服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def get_coffee_shop_recommendations(
        self, 
        request: CoffeeShopRecommendationRequest
    ) -> CoffeeShopRecommendationResponse:
        """
        获取咖啡店推荐
        
        Args:
            request: 推荐请求参数
            
        Returns:
            咖啡店推荐响应
        """
        # 获取用户画像数据
        user_profile = self._get_user_profile_by_card_id(request.user_card_id)
        
        # 生成咖啡店数据
        coffee_shops = self._generate_coffee_shops_data(request.location)
        
        # 基于用户画像进行智能推荐
        recommendations = self._rank_coffee_shops(
            coffee_shops, 
            user_profile, 
            request
        )
        
        # 选择主推荐和备选
        main_recommendation = recommendations[0] if recommendations else None
        alternative_options = recommendations[1:4] if len(recommendations) > 1 else []
        
        # 生成用户画像匹配分析
        profile_match = self._generate_profile_match_analysis(
            user_profile, 
            main_recommendation, 
            request
        )
        
        return CoffeeShopRecommendationResponse(
            main_recommendation=main_recommendation,
            alternative_options=alternative_options,
            user_profile_match=profile_match,
            recommendation_strategy=self._generate_recommendation_strategy(request),
            total_found=len(coffee_shops)
        )
    
    def _get_user_profile_by_card_id(self, user_card_id: str) -> Optional[Dict[str, Any]]:
        """通过用户卡片ID获取用户画像"""
        try:
            # 获取用户卡片信息
            card = UserCardService.get_card_by_id(self.db, user_card_id)
            if not card:
                return None
                
            # 获取用户画像
            user_profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == card.user_id
            ).first()
            
            if user_profile and user_profile.raw_profile:
                return json.loads(user_profile.raw_profile)
            return None
        except Exception as e:
            print(f"获取用户画像失败: {e}")
            return None
    
    def _generate_coffee_shops_data(self, location: str) -> List[Dict[str, Any]]:
        """生成咖啡店数据"""
        base_coffee_shops = [
            {
                "name": "星巴克",
                "address": f"{location}购物中心店",
                "distance": "500m",
                "walking_time": "步行8分钟",
                "rating": 4.3,
                "price_range": "¥35-50",
                "coffee_types": ["拿铁", "卡布奇诺", "美式咖啡", "星冰乐"],
                "features": ["环境舒适", "免费WiFi", "充电插座", "连锁品牌"],
                "image": "/images/coffee-shop-starbucks.jpg",
                "location": {"latitude": 31.2304, "longitude": 121.4737},
                "atmosphere_tags": ["商务", "现代", "安静"],
                "crowd_type": "商务人士和学生",
                "best_visit_time": "下午2-5点"
            },
            {
                "name": "瑞幸咖啡",
                "address": f"{location}商务楼店",
                "distance": "300m",
                "walking_time": "步行5分钟",
                "rating": 4.1,
                "price_range": "¥15-25",
                "coffee_types": ["生椰拿铁", "厚乳拿铁", "美式", "小鹿茶"],
                "features": ["性价比高", "快速出餐", "小程序点餐", "外卖配送"],
                "image": "/images/coffee-shop-luckin.jpg",
                "location": {"latitude": 31.2304, "longitude": 121.4737},
                "atmosphere_tags": ["快捷", "年轻", "活力"],
                "crowd_type": "年轻白领和学生",
                "best_visit_time": "上午9-11点，下午3-6点"
            },
            {
                "name": "精品咖啡馆",
                "address": f"{location}文化街区店",
                "distance": "800m",
                "walking_time": "步行12分钟",
                "rating": 4.6,
                "price_range": "¥40-60",
                "coffee_types": ["手冲咖啡", "单品咖啡", "拿铁", "卡布奇诺"],
                "features": ["精品咖啡", "安静环境", "适合聊天", "咖啡师专业"],
                "image": "/images/coffee-shop-specialty.jpg",
                "location": {"latitude": 31.2304, "longitude": 121.4737},
                "atmosphere_tags": ["文艺", "安静", "品质"],
                "crowd_type": "咖啡爱好者和文艺青年",
                "best_visit_time": "下午3-6点，晚上7-9点"
            },
            {
                "name": "太平洋咖啡",
                "address": f"{location}商业街店",
                "distance": "600m",
                "walking_time": "步行10分钟",
                "rating": 4.2,
                "price_range": "¥30-45",
                "coffee_types": ["拿铁", "摩卡", "美式", "冰咖啡"],
                "features": ["连锁品牌", "稳定品质", "环境舒适", "服务周到"],
                "image": "/images/coffee-shop-pacific.jpg",
                "location": {"latitude": 31.2304, "longitude": 121.4737},
                "atmosphere_tags": ["温馨", "舒适", "可靠"],
                "crowd_type": "家庭客群和上班族",
                "best_visit_time": "上午10-12点，下午2-4点"
            },
            {
                "name": "猫屎咖啡",
                "address": f"{location}高档商场店",
                "distance": "1.2km",
                "walking_time": "步行18分钟",
                "rating": 4.4,
                "price_range": "¥50-80",
                "coffee_types": ["猫屎咖啡", "蓝山咖啡", "拿铁", "卡布奇诺"],
                "features": ["高端咖啡", "独特体验", "奢华环境", "VIP服务"],
                "image": "/images/coffee-shop-luxury.jpg",
                "location": {"latitude": 31.2304, "longitude": 121.4737},
                "atmosphere_tags": ["奢华", "独特", "高端"],
                "crowd_type": "高端消费者和商务人士",
                "best_visit_time": "下午3-6点，晚上7-9点"
            },
            {
                "name": "漫咖啡",
                "address": f"{location}创意园区店",
                "distance": "900m",
                "walking_time": "步行15分钟",
                "rating": 4.3,
                "price_range": "¥25-40",
                "coffee_types": ["拿铁", "美式", "摩卡", "焦糖玛奇朵"],
                "features": ["文艺氛围", "书吧结合", "安静角落", "创意装饰"],
                "image": "/images/coffee-shop-artistic.jpg",
                "location": {"latitude": 31.2304, "longitude": 121.4737},
                "atmosphere_tags": ["文艺", "安静", "创意"],
                "crowd_type": "文艺青年和自由职业者",
                "best_visit_time": "下午2-6点，晚上7-9点"
            }
        ]
        
        return base_coffee_shops
    
    def _rank_coffee_shops(
        self, 
        coffee_shops: List[Dict[str, Any]], 
        user_profile: Optional[Dict[str, Any]], 
        request: CoffeeShopRecommendationRequest
    ) -> List[CoffeeShopRecommendation]:
        """基于用户画像对咖啡店进行智能排序"""
        
        scored_shops = []
        
        for shop in coffee_shops:
            # 计算匹配分数
            match_score = self._calculate_match_score(shop, user_profile, request)
            
            # 生成个性化推荐理由
            recommendation_reason = self._generate_recommendation_reason(
                shop, user_profile, request, match_score
            )
            
            # 创建推荐对象
            recommendation = CoffeeShopRecommendation(
                name=shop["name"],
                address=shop["address"],
                distance=shop["distance"],
                walking_time=shop["walking_time"],
                rating=shop["rating"],
                price_range=shop["price_range"],
                coffee_types=shop["coffee_types"],
                features=shop["features"],
                image=shop["image"],
                location=shop["location"],
                recommendation_reason=recommendation_reason,
                match_score=match_score,
                atmosphere_tags=shop["atmosphere_tags"],
                crowd_type=shop["crowd_type"],
                best_visit_time=shop["best_visit_time"]
            )
            
            scored_shops.append(recommendation)
        
        # 按匹配分数排序
        scored_shops.sort(key=lambda x: x.match_score, reverse=True)
        return scored_shops
    
    def _calculate_match_score(
        self, 
        shop: Dict[str, Any], 
        user_profile: Optional[Dict[str, Any]], 
        request: CoffeeShopRecommendationRequest
    ) -> int:
        """计算咖啡店与用户画像的匹配分数"""
        
        score = 50  # 基础分数
        
        # 基于用户画像的评分
        if user_profile:
            # 年龄匹配
            age = user_profile.get("age", 25)
            if 20 <= age <= 30:
                if "年轻" in shop["crowd_type"] or "学生" in shop["crowd_type"]:
                    score += 15
            elif 30 < age <= 45:
                if "商务" in shop["crowd_type"] or "上班族" in shop["crowd_type"]:
                    score += 15
            
            # 兴趣匹配
            interests = user_profile.get("interests", [])
            for interest in interests:
                if interest in shop["atmosphere_tags"] or interest in shop["features"]:
                    score += 10
            
            # 职业匹配
            occupation = user_profile.get("occupation", "")
            if "自由职业" in occupation and "自由职业者" in shop["crowd_type"]:
                score += 10
            elif "商务" in occupation and "商务" in shop["crowd_type"]:
                score += 10
        
        # 基于请求参数的评分
        if request.coffee_preferences:
            for coffee_type in request.coffee_preferences:
                if coffee_type in shop["coffee_types"]:
                    score += 10
                    break
        
        if request.atmosphere_preferences:
            for preference in request.atmosphere_preferences:
                if preference in shop["atmosphere_tags"] or preference in shop["features"]:
                    score += 10
                    break
        
        # 预算匹配
        if request.budget_range:
            if "¥15-25" in request.budget_range and shop["price_range"] == "¥15-25":
                score += 15
            elif "¥25-40" in request.budget_range and shop["price_range"] in ["¥25-40", "¥15-25"]:
                score += 10
            elif "¥40-60" in request.budget_range and shop["price_range"] in ["¥40-60", "¥30-45"]:
                score += 5
        
        # 距离评分
        if "300m" in shop["distance"]:
            score += 10
        elif "500m" in shop["distance"]:
            score += 8
        elif "600-800m" in shop["distance"]:
            score += 5
        
        # 评分加成
        if shop["rating"] >= 4.5:
            score += 10
        elif shop["rating"] >= 4.0:
            score += 5
        
        return min(score, 100)  # 最高100分
    
    def _generate_recommendation_reason(
        self, 
        shop: Dict[str, Any], 
        user_profile: Optional[Dict[str, Any]], 
        request: CoffeeShopRecommendationRequest,
        match_score: int
    ) -> str:
        """生成个性化推荐理由"""
        
        reasons = []
        
        # 基于用户画像的推荐理由
        if user_profile:
            age = user_profile.get("age", 25)
            interests = user_profile.get("interests", [])
            occupation = user_profile.get("occupation", "")
            
            if 20 <= age <= 30:
                reasons.append(f"适合{age}岁年轻人的活力氛围")
            elif 30 < age <= 45:
                reasons.append(f"符合{age}岁成熟人士的品味选择")
            
            if interests:
                matched_interests = [interest for interest in interests 
                                   if interest in shop["atmosphere_tags"] or interest in shop["features"]]
                if matched_interests:
                    reasons.append(f"与你的{', '.join(matched_interests)}兴趣相契合")
            
            if occupation and ("商务" in occupation or "管理" in occupation):
                if "商务" in shop["crowd_type"]:
                    reasons.append("商务人士的理想选择")
        
        # 基于请求参数的推荐理由
        if request.coffee_preferences:
            matched_coffees = [coffee for coffee in request.coffee_preferences 
                             if coffee in shop["coffee_types"]]
            if matched_coffees:
                reasons.append(f"提供你喜爱的{', '.join(matched_coffees)}")
        
        if request.atmosphere_preferences:
            matched_atmosphere = [atm for atm in request.atmosphere_preferences 
                                if atm in shop["atmosphere_tags"] or atm in shop["features"]]
            if matched_atmosphere:
                reasons.append(f"拥有你偏好的{', '.join(matched_atmosphere)}氛围")
        
        # 通用推荐理由
        if "300m" in shop["distance"]:
            reasons.append("距离超近，步行仅需5分钟")
        elif "500m" in shop["distance"]:
            reasons.append("距离适中，步行8分钟即达")
        
        if shop["rating"] >= 4.5:
            reasons.append(f"评分高达{shop['rating']}分，品质卓越")
        elif shop["rating"] >= 4.0:
            reasons.append(f"评分{shop['rating']}分，口碑良好")
        
        # 特色推荐理由
        if "精品咖啡" in shop["features"]:
            reasons.append("专业咖啡师精心制作，品质保证")
        if "环境舒适" in shop["features"]:
            reasons.append("环境舒适，适合聊天约会")
        if "性价比高" in shop["features"]:
            reasons.append("性价比极高，物超所值")
        
        if not reasons:
            reasons.append("综合条件优秀，值得推荐")
        
        return "；".join(reasons[:3]) + "。"  # 最多3个理由
    
    def _generate_profile_match_analysis(
        self, 
        user_profile: Optional[Dict[str, Any]], 
        main_recommendation: Optional[CoffeeShopRecommendation], 
        request: CoffeeShopRecommendationRequest
    ) -> Dict[str, Any]:
        """生成用户画像匹配分析"""
        
        analysis = {
            "user_profile_available": user_profile is not None,
            "match_score": main_recommendation.match_score if main_recommendation else 0,
            "key_matching_factors": [],
            "personalization_level": "基础" if not user_profile else "个性化"
        }
        
        if user_profile and main_recommendation:
            factors = []
            
            # 年龄匹配
            age = user_profile.get("age", 25)
            if 20 <= age <= 30 and "年轻" in main_recommendation.crowd_type:
                factors.append("年龄群体匹配")
            elif 30 < age <= 45 and "商务" in main_recommendation.crowd_type:
                factors.append("职业背景匹配")
            
            # 兴趣匹配
            interests = user_profile.get("interests", [])
            matched_interests = [interest for interest in interests 
                               if interest in main_recommendation.atmosphere_tags]
            if matched_interests:
                factors.append(f"兴趣匹配({len(matched_interests)}项)")
            
            # 预算匹配
            if request.budget_range and main_recommendation.price_range in request.budget_range:
                factors.append("预算范围匹配")
            
            # 距离偏好
            if main_recommendation.match_score >= 80:
                factors.append("高匹配度")
            
            analysis["key_matching_factors"] = factors
        
        return analysis
    
    def _generate_recommendation_strategy(self, request: CoffeeShopRecommendationRequest) -> str:
        """生成推荐策略说明"""
        
        strategy_parts = []
        
        if request.coffee_preferences:
            strategy_parts.append(f"优先考虑{', '.join(request.coffee_preferences)}咖啡类型")
        
        if request.atmosphere_preferences:
            strategy_parts.append(f"匹配{', '.join(request.atmosphere_preferences)}氛围")
        
        if request.budget_range:
            strategy_parts.append(f"控制在{request.budget_range}预算范围内")
        
        if request.max_distance and request.max_distance < 1000:
            strategy_parts.append(f"距离限制在{request.max_distance}米内")
        
        strategy_parts.append("综合评分、距离、用户评价等因素")
        
        return "；".join(strategy_parts)