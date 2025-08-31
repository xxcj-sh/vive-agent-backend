#!/usr/bin/env python3
"""
快速用户查询脚本
简单快速地查看数据库中的用户信息
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User


def quick_user_summary():
    """快速显示用户摘要信息"""
    db: Session = next(get_db())
    try:
        users = db.query(User).all()
        
        print("=" * 100)
        print(f"{'ID':<5} {'OpenID':<25} {'昵称':<15} {'性别':<5} {'年龄':<5} {'激活状态':<8} {'创建时间':<20}")
        print("=" * 100)
        
        if not users:
            print("数据库中暂无用户数据")
            return
        
        for user in users:
            created_time = user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else 'N/A'
            print(f"{user.id:<5} {user.wechat_openid[:24]:<25} {(user.nickname or 'N/A')[:14]:<15} "
                  f"{user.gender or 'N/A':<5} {user.age or 'N/A':<5} "
                  f"{'是' if user.is_active else '否':<8} {created_time:<20}")
        
        print("=" * 100)
        print(f"总计: {len(users)} 个用户")
        
    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    quick_user_summary()