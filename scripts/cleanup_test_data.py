#!/usr/bin/env python3
"""
清理测试数据
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.utils.db_config import get_db
from app.models.user_card_db import UserCard

def cleanup_test_data():
    """清理测试用户卡片数据"""
    db: Session = next(get_db())
    
    try:
        # 删除测试用户的卡片
        deleted_count = db.query(UserCard).filter(
            UserCard.user_id.like('test_user_%')
        ).delete()
        
        db.commit()
        print(f"✅ 已删除 {deleted_count} 个测试卡片")
        
        # 验证删除结果
        remaining = db.query(UserCard).filter(
            UserCard.user_id.like('test_user_%')
        ).count()
        print(f"📊 剩余测试卡片: {remaining}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 清理失败: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_test_data()