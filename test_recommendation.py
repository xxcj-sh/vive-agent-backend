#!/usr/bin/env python3
"""
测试推荐算法功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.services.user_connection_service import UserConnectionService
from app.database import SessionLocal

def test_recommendation_algorithm():
    """测试推荐算法"""
    print("🧪 开始测试推荐算法...")
    
    # 测试用户ID（假设存在）
    test_user_id = 1
    
    try:
        # 获取数据库会话
        db = SessionLocal()
        
        # 调用推荐算法
        recommended_users = UserConnectionService.get_recommended_users(db=db, current_user_id=test_user_id)
        
        print(f"✅ 推荐算法调用成功！")
        print(f"📊 为用户 {test_user_id} 推荐了 {len(recommended_users)} 个用户")
        
        if recommended_users:
            print("📝 推荐用户列表:")
            for i, user in enumerate(recommended_users[:5]):  # 只显示前5个
                print(f"  {i+1}. 用户ID: {user.get('id', 'N/A')}, "
                      f"姓名: {user.get('nick_name', 'N/A')}, "
                      f"年龄: {user.get('age', 'N/A')}, "
                      f"职业: {user.get('occupation', 'N/A')}")
        else:
            print("ℹ️  暂无推荐用户")
            
        return True
        
    except Exception as e:
        print(f"❌ 推荐算法测试失败: {str(e)}")
        return False
    finally:
        # 关闭数据库连接
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    success = test_recommendation_algorithm()
    sys.exit(0 if success else 1)