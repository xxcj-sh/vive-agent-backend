#!/usr/bin/env python3
"""
测试 DataService.get_cards 方法
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量
os.environ.setdefault('ENVIRONMENT', 'development')

from app.services.data_adapter import DataService

def test_get_cards():
    """测试获取卡片数据"""
    print("🧪 测试 DataService.get_cards 方法...")
    
    try:
        data_service = DataService()
        
        # 测试不同类型的卡片获取
        test_cases = [
            ("dating", "seeker", 1, 10),
            ("housing", "seeker", 1, 10),
            ("housing", "provider", 1, 10),
            ("activity", "participant", 1, 10),
            ("activity", "organizer", 1, 10),
        ]
        
        for match_type, user_role, page, page_size in test_cases:
            print(f"\n📋 测试: {match_type} - {user_role}")
            try:
                result = data_service.get_cards(match_type, user_role, page, page_size)
                print(f"   ✅ 成功获取 {result['total']} 条记录")
                print(f"   📄 第 {result['page']} 页，每页 {result['pageSize']} 条")
                print(f"   🔍 策略: {result['strategy']}")
                if result['list']:
                    print(f"   👤 示例用户: {result['list'][0]['nickName']}")
                else:
                    print("   📭 暂无数据")
            except Exception as e:
                print(f"   ❌ 失败: {str(e)}")
        
        print("\n🎉 测试完成！")
        
    except Exception as e:
        print(f"💥 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_cards()