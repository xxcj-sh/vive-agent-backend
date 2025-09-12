"""
社交场景使用示例
展示如何使用新的社交场景功能
"""

import requests
import json
from typing import Dict, Any

class SocialExample:
    """社交场景使用示例类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def create_social_profile_example(self, user_id: int) -> Dict[str, Any]:
        """创建社交档案示例"""
        
        profile_data = {
            "headline": "资深全栈工程师 | 技术领导者",
            "summary": "拥有8年全栈开发经验，专注于微服务架构和云原生应用。目前在一家独角兽公司担任技术团队负责人，热衷于技术分享和人才培养。擅长Python、JavaScript、React和Kubernetes。",
            "current_role": "技术团队负责人",
            "current_company": "科技独角兽公司",
            "industry": "互联网/科技",
            "professional_level": "senior_level",
            "company_size": "large",
            "years_of_experience": 8,
            "skills": [
                "Python", "JavaScript", "React", "Node.js", "Kubernetes", 
                "微服务架构", "云原生", "团队管理", "技术领导力"
            ],
            "expertise_areas": [
                "分布式系统", "微服务架构", "云原生技术", "技术团队管理"
            ],
            "social_interests": [
                "technology", "startup", "mentorship", "career_development"
            ],
            "value_offerings": [
                "技术团队管理经验分享", "微服务架构最佳实践", "职业发展规划指导"
            ],
            "seeking_opportunities": [
                "技术顾问合作", "创业伙伴", "技术社区演讲机会"
            ],
            "activity_level": "high"
        }
        
        response = requests.post(
            f"{self.base_url}/api/social/profile",
            params={"user_id": user_id},
            json=profile_data
        )
        
        return response.json()
    
    def create_social_preference_example(self, user_id: int) -> Dict[str, Any]:
        """创建社交偏好设置示例"""
        
        preference_data = {
            "social_purpose": [
                "networking", "mentorship", "knowledge_sharing", "career_advice"
            ],
            "social_interests": [
                "technology", "startup", "career_development", "leadership"
            ],
            "experience_level_preference": [
                "mid_level", "senior_level", "executive"
            ],
            "company_size_preference": [
                "startup", "medium", "large"
            ],
            "target_industries": [
                "互联网/科技", "人工智能", "金融科技", "企业服务"
            ],
            "preferred_locations": [
                "北京", "上海", "深圳", "杭州"
            ],
            "skills_to_learn": [
                "Go语言", "机器学习", "产品管理", "投资知识"
            ],
            "skills_to_share": [
                "Python高级编程", "团队管理经验", "技术架构设计"
            ],
            "remote_preference": True,
            "activity_types": [
                "coffee_chat", "workshop", "conference", "online_webinar"
            ]
        }
        
        response = requests.post(
            f"{self.base_url}/api/social/preferences",
            params={"user_id": user_id},
            json=preference_data
        )
        
        return response.json()
    
    def create_match_criteria_example(self, user_id: int) -> Dict[str, Any]:
        """创建匹配标准示例"""
        
        criteria_data = {
            "min_experience_level": "mid_level",
            "max_experience_level": "executive",
            "preferred_company_sizes": ["startup", "medium", "large"],
            "must_have_skills": ["Python", "JavaScript"],
            "preferred_industries": [
                "互联网/科技", "人工智能", "金融科技"
            ],
            "location_radius_km": 100,
            "min_mutual_connections": 1,
            "activity_level_threshold": "medium"
        }
        
        response = requests.post(
            f"{self.base_url}/api/social/match-criteria",
            params={"user_id": user_id},
            json=criteria_data
        )
        
        return response.json()
    
    def get_social_matches_example(self, user_id: int, limit: int = 5) -> Dict[str, Any]:
        """获取社交匹配示例"""
        
        response = requests.get(
            f"{self.base_url}/api/social/matches",
            params={"user_id": user_id, "limit": limit}
        )
        
        return response.json()
    
    def get_social_analytics_example(self, user_id: int) -> Dict[str, Any]:
        """获取社交分析数据示例"""
        
        response = requests.get(
            f"{self.base_url}/api/social/analytics",
            params={"user_id": user_id}
        )
        
        return response.json()
    
    def search_social_profiles_example(self, keyword: str = "Python") -> Dict[str, Any]:
        """搜索社交档案示例"""
        
        response = requests.get(
            f"{self.base_url}/api/social/search",
            params={"keyword": keyword, "limit": 10}
        )
        
        return response.json()
    
    def get_social_enums_example(self) -> Dict[str, Any]:
        """获取社交场景枚举值示例"""
        
        response = requests.get(f"{self.base_url}/api/social/enums")
        return response.json()

def run_full_example():
    """运行完整的使用示例"""
    
    example = SocialExample()
    
    print("🚀 开始社交场景使用示例...")
    
    try:
        # 1. 获取枚举值
        print("\n📋 获取社交场景枚举值...")
        enums = example.get_social_enums_example()
        print(f"可用枚举: {json.dumps(enums, indent=2, ensure_ascii=False)}")
        
        # 2. 创建社交档案
        print("\n👤 创建社交档案...")
        profile_result = example.create_social_profile_example(1)
        print(f"档案创建结果: {json.dumps(profile_result, indent=2, ensure_ascii=False)}")
        
        # 3. 创建社交偏好
        print("\n⚙️ 创建社交偏好设置...")
        preference_result = example.create_social_preference_example(1)
        print(f"偏好设置结果: {json.dumps(preference_result, indent=2, ensure_ascii=False)}")
        
        # 4. 创建匹配标准
        print("\n🎯 创建匹配标准...")
        criteria_result = example.create_match_criteria_example(1)
        print(f"匹配标准结果: {json.dumps(criteria_result, indent=2, ensure_ascii=False)}")
        
        # 5. 获取社交分析
        print("\n📊 获取社交分析数据...")
        analytics_result = example.get_social_analytics_example(1)
        print(f"分析数据结果: {json.dumps(analytics_result, indent=2, ensure_ascii=False)}")
        
        # 6. 搜索社交档案
        print("\n🔍 搜索社交档案...")
        search_result = example.search_social_profiles_example("Python")
        print(f"搜索结果: {json.dumps(search_result, indent=2, ensure_ascii=False)}")
        
        # 7. 获取匹配推荐
        print("\n❤️ 获取社交匹配推荐...")
        matches_result = example.get_social_matches_example(1, 3)
        print(f"匹配推荐: {json.dumps(matches_result, indent=2, ensure_ascii=False)}")
        
        print("\n✅ 社交场景使用示例完成！")
        
    except Exception as e:
        print(f"❌ 示例运行失败: {str(e)}")
        print("请确保服务器已启动: uvicorn app.main:app --reload")

if __name__ == "__main__":
    run_full_example()