#!/usr/bin/env python3
"""
使用真实用户ID测试推荐系统
"""
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.match_service import MatchService
from app.database import SessionLocal

def test_with_real_user():
    """使用真实用户ID测试推荐系统"""
    print("🧪 使用真实用户测试推荐系统...")
    
    # 使用数据库中的真实用户ID
    real_user_id = "d204f73d-3a5f-4b8b-9e6a-7e8a3d5c7b9e"
    
    test_cases = [
        ("dating", "seeker"),
        ("dating", "provider"),
        ("housing", "seeker"),
        ("housing", "provider"),
        ("activity", "participant"),
        ("activity", "organizer"),
    ]
    
    db = SessionLocal()
    try:
        service = MatchService(db)
        
        # 首先检查用户是否存在
        from app.models.user import User
        user = db.query(User).filter(User.id == real_user_id).first()
        if user:
            print(f"✅ 找到用户: {user.id}, 昵称: {getattr(user, 'nick_name', None) or getattr(user, 'name', '匿名')}")
        else:
            print(f"❌ 未找到用户: {real_user_id}")
            
        # 检查所有用户
        all_users = db.query(User).all()
        print(f"数据库中共有 {len(all_users)} 个用户:")
        for u in all_users:
            print(f"  - {u.id}: {getattr(u, 'nick_name', None) or getattr(u, 'name', '匿名')}")
        
        for scene_type, user_role in test_cases:
            print(f"\n=== 测试场景: {scene_type} - {user_role} ===")
            
            try:
                result = service.get_recommendation_cards(
                    user_id=real_user_id,
                    scene_type=scene_type,
                    user_role=user_role,
                    page=1,
                    page_size=10
                )
                
                print(f"结果类型: {type(result)}")
                if hasattr(result, '__len__'):
                    print(f"✅ 成功获取 {len(result)} 张卡片")
                    
                    # 转换为列表如果还不是
                    if isinstance(result, dict):
                        cards = result.get('cards', [])
                        print(f"卡片数据在 'cards' 键中: {len(cards)} 张")
                    else:
                        cards = list(result) if result else []
                    
                    if cards:
                        print("📊 前3张卡片示例:")
                        for i, card in enumerate(cards[:3]):
                            print(f"   {i+1}. {card.get('title', '无标题')} - {card.get('user_id', '未知用户')}")
                            if i == 0:  # 打印第一张卡片的完整结构
                                print(f"      完整结构: {json.dumps(card, ensure_ascii=False, indent=2)[:200]}...")
                    else:
                        print("🤔 卡片列表为空")
                        if isinstance(result, dict):
                            print(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                else:
                    print(f"🤔 结果不可迭代: {result}")
                    
            except Exception as e:
                print(f"❌ 错误: {e}")
                import traceback
                traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_with_real_user()