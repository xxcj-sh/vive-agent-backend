#!/usr/bin/env python3
"""
测试推荐系统调试日志
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('ENVIRONMENT', 'development')

from app.services.match_service import MatchService
from app.database import SessionLocal
from sqlalchemy.orm import Session

def test_recommendations():
    """测试推荐系统"""
    print("🧪 测试推荐系统调试日志...")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        match_service = MatchService(db)
        
        # 测试参数
        test_cases = [
            {"user_id": "test_user_001", "scene_type": "dating", "user_role": "seeker", "page": 1, "page_size": 5},
            {"user_id": "test_user_001", "scene_type": "housing", "user_role": "seeker", "page": 1, "page_size": 5},
            {"user_id": "test_user_001", "scene_type": "activity", "user_role": "participant", "page": 1, "page_size": 5},
        ]
        
        for case in test_cases:
            print(f"\n=== 测试场景: {case['scene_type']} - {case['user_role']} ===")
            try:
                result = match_service.get_recommendation_cards(**case)
                print(f"✅ 成功获取 {len(result.get('cards', []))} 张卡片")
                print(f"📊 总数: {result.get('total', 0)}")
                
                if result.get('cards'):
                    print(f"📋 示例卡片: {result['cards'][0].get('name', '匿名用户')}")
                    
            except Exception as e:
                print(f"❌ 失败: {str(e)}")
                import traceback
                traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_recommendations()