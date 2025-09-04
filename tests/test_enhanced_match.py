"""
增强匹配服务测试
"""

import sys
from pathlib import Path
from unittest.mock import Mock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.enhanced_match_service import MatchCompatibilityCalculator


def test_housing_compatibility():
    """测试房源匹配兼容性计算"""
    calculator = MatchCompatibilityCalculator()
    
    # 房东资料
    landlord_profile = {
        'housing_price': 5000,
        'location': '朝阳区',
        'housing_type': '整租',
        'housing_lease_term': '一年'
    }
    
    # 租客资料
    tenant_profile = {
        'housing_budget_min': 4500,
        'housing_budget_max': 5500,
        'preferred_location': '朝阳区',
        'preferred_housing_type': '整租',
        'housing_lease_duration': '一年'
    }
    
    score = calculator._calculate_housing_compatibility(landlord_profile, tenant_profile)
    print(f"房源匹配兼容性分数: {score}")
    assert score >= 80, f"期望分数 >= 80, 实际分数: {score}"


def test_dating_compatibility():
    """测试交友匹配兼容性计算"""
    calculator = MatchCompatibilityCalculator()
    
    user1_profile = {
        'age': 28,
        'interests': '旅行,摄影,音乐',
        'location': '北京市朝阳区',
        'education': '本科'
    }
    
    user2_profile = {
        'age': 26,
        'interests': '旅行,音乐,电影',
        'location': '北京市朝阳区',
        'education': '本科'
    }
    
    score = calculator._calculate_dating_compatibility(user1_profile, user2_profile)
    print(f"交友匹配兼容性分数: {score}")
    assert score >= 70, f"期望分数 >= 70, 实际分数: {score}"


if __name__ == "__main__":
    print("开始测试增强匹配服务...")
    test_housing_compatibility()
    test_dating_compatibility()
    print("测试完成！")